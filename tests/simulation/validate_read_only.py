"""MAMBA-26/27 acceptance over real stdio MCP and loopback ArduPilot SITL.

Run with the simulation dependency group. Only the supplied local SITL binary
is launched; no arming, movement, vehicle parameter writes, or hardware I/O.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time

from importlib.metadata import version
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pymavlink.dialects.v20 import ardupilotmega as mavlink

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ["position", "velocity", "battery", "gps", "health"]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def check(condition, detail):
    if not condition:
        raise AssertionError(detail)


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Router(asyncio.DatagramProtocol):
    """Decode independent observations and selectively forward whole frames."""

    def __init__(self, mamba_port):
        self.mamba_address = ("127.0.0.1", mamba_port)
        self.simulator_address = None
        self.parser = mavlink.MAVLink(None)
        self.parser.robust_parsing = True
        self.blocked = set()
        self.blackout = False
        self.observations = []
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        if address == self.mamba_address:
            if self.simulator_address and not self.blackout:
                self.transport.sendto(data, self.simulator_address)
            return
        self.simulator_address = address
        for message in self.parser.parse_buffer(data) or []:
            name = message.get_type()
            if name == "BAD_DATA":
                continue
            self.observations.append({
                "received_at": utc_now(), "monotonic": time.monotonic(),
                "system_id": message.get_srcSystem(),
                "component_id": message.get_srcComponent(),
                "message": message.to_dict(),
            })
            if not self.blackout and name not in self.blocked:
                self.transport.sendto(bytes(message.get_msgbuf()), self.mamba_address)

    async def wait_for(self, name, timeout=60):
        async with asyncio.timeout(timeout):
            while not any(o["message"]["mavpackettype"] == name for o in self.observations):
                await asyncio.sleep(.1)

    def nearest(self, name, timestamp):
        observed = datetime.fromisoformat(timestamp).timestamp()
        candidates = [o for o in self.observations
                      if o["system_id"] == 1 and o["component_id"] == 1
                      and o["message"]["mavpackettype"] == name]
        check(bool(candidates), f"No independent {name} observation")
        result = min(candidates, key=lambda o: abs(
            datetime.fromisoformat(o["received_at"]).timestamp() - observed))
        age = abs(datetime.fromisoformat(result["received_at"]).timestamp() - observed)
        check(age < 3, f"Independent {name} observation differs by {age:.3f}s")
        return result


async def call(session, name, arguments=None):
    started = time.monotonic()
    result = await session.call_tool(name, arguments or {})
    text = result.content[0].text
    return {"tool": name, "arguments": arguments or {}, "observed_at": utc_now(),
            "elapsed_s": round(time.monotonic() - started, 3),
            "is_error": result.isError,
            "value": text if result.isError or name == "ping" else json.loads(text)}


async def wait_state(session, wanted, timeout=45):
    history = []
    async with asyncio.timeout(timeout):
        while True:
            result = await call(session, "get_vehicle_status")
            check(not result["is_error"], result)
            if not history or result["value"]["state"] != history[-1]["value"]["state"]:
                history.append(result)
            if result["value"]["state"] == wanted:
                return history
            await asyncio.sleep(.2)


@asynccontextmanager
async def session_for(output, config, label):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "src/mamba/server.py"), "--config", str(config)],
    )
    with (output / f"mcp-{label}.log").open("w") as diagnostics:
        async with stdio_client(parameters, errlog=diagnostics) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


def compare(router, information, telemetry):
    check(not information["is_error"], information)
    check(not telemetry["is_error"], telemetry)
    info, data = information["value"], telemetry["value"]
    check(info["system_id"] == data["system_id"] == 1, (info, data))
    check(not info["data"]["errors"] and not data["errors"], (info, data))
    check(set(data["readings"]) == set(FIELDS), data)
    comparisons = []

    def equal(category, field, message, wire_field, scale=1, tolerance=0):
        sample = data["readings"][category]
        observation = router.nearest(message, sample["received_at"])
        expected = observation["message"][wire_field] * scale
        actual = sample["data"][field]
        check(actual is not None and math.isclose(actual, expected, abs_tol=tolerance),
              f"{category}.{field}: {actual} != {expected} (+/- {tolerance})")
        comparisons.append({"field": f"{category}.{field}", "actual": actual,
                            "expected": expected, "tolerance": tolerance,
                            "reference": observation})

    equal("position", "latitude_deg", "GLOBAL_POSITION_INT", "lat", 1e-7, 1e-5)
    equal("position", "longitude_deg", "GLOBAL_POSITION_INT", "lon", 1e-7, 1e-5)
    equal("position", "absolute_altitude_m", "GLOBAL_POSITION_INT", "alt", .001, .5)
    equal("position", "relative_altitude_m", "GLOBAL_POSITION_INT", "relative_alt", .001, .5)
    for field, wire in [("north_m_s", "vx"), ("east_m_s", "vy"), ("down_m_s", "vz")]:
        equal("velocity", field, "GLOBAL_POSITION_INT", wire, .01, .15)
    equal("battery", "voltage_v", "SYS_STATUS", "voltage_battery", .001, .1)
    equal("battery", "remaining_percent", "SYS_STATUS", "battery_remaining", 1, 1)
    equal("gps", "num_satellites", "GPS_RAW_INT", "satellites_visible")
    gps = data["readings"]["gps"]
    raw_gps = router.nearest("GPS_RAW_INT", gps["received_at"])
    fixes = {0: "NO_GPS", 1: "NO_FIX", 2: "FIX_2D", 3: "FIX_3D",
             4: "FIX_DGPS", 5: "RTK_FLOAT", 6: "RTK_FIXED"}
    check(gps["data"]["fix_type"] == fixes[raw_gps["message"]["fix_type"]], gps)
    health = data["readings"]["health"]["data"]
    check(all(isinstance(value, bool) for value in health.values()), health)
    check(health["is_global_position_ok"] and health["is_local_position_ok"]
          and health["is_home_position_ok"], health)
    # SITL remains disarmed throughout. is_armable also depends on pre-arm checks,
    # so do not infer it from GPS or duplicate MAVSDK's health calculation here.
    heartbeat = router.nearest("HEARTBEAT", data["readings"]["health"]["received_at"])
    check(not heartbeat["message"]["base_mode"] & mavlink.MAV_MODE_FLAG_SAFETY_ARMED,
          "SITL unexpectedly armed")
    version_observation = router.nearest("AUTOPILOT_VERSION", info["received_at"])
    raw = version_observation["message"]
    packed = raw["flight_sw_version"]
    for field, expected in {"flight_sw_major": packed >> 24,
                            "flight_sw_minor": packed >> 16 & 255,
                            "flight_sw_patch": packed >> 8 & 255}.items():
        check(info["data"]["version"][field] == expected, info)
    check(info["data"]["identification"]["legacy_uid"] == raw["uid"], info)
    check(info["data"]["identification"]["hardware_uid"] == bytes(raw["uid2"]).hex(), info)
    comparisons.append({"field": "information.version/legacy_uid",
                        "actual": info["data"], "reference": version_observation})
    return comparisons


async def validate(args, report, router, config):
    async with session_for(args.output, config, "baseline") as session:
        report["startup"] = await wait_state(session, "connected")
        # Wait for estimator/home initialization while continuing to collect wire data.
        for attempt in range(30):
            telemetry = await call(session, "get_vehicle_telemetry", {"fields": FIELDS})
            if (not telemetry["is_error"] and not telemetry["value"]["errors"]
                    and telemetry["value"]["readings"]["health"]["data"]["is_home_position_ok"]):
                break
            await asyncio.sleep(1)
        information = await call(session, "get_vehicle_information")
        report["information"] = information
        report["telemetry"] = telemetry
        report["comparisons"] = compare(router, information, telemetry)
        selected = await call(session, "get_vehicle_telemetry", {"fields": ["battery"]})
        check(not selected["is_error"] and set(selected["value"]["readings"]) == {"battery"}, selected)
        report["selective"] = selected
        report["persistent"] = await call(session, "get_vehicle_status")
        check(report["persistent"]["value"]["state"] == "connected", report["persistent"])

    # Each fault uses a fresh native SDK so retained SDK state cannot mask a
    # missing wire topic. This tests acquisition availability, not source age.
    router.blocked = {"GLOBAL_POSITION_INT"}
    async with session_for(args.output, config, "missing-position") as session:
        await wait_state(session, "connected")
        partial = await call(session, "get_vehicle_telemetry", {"fields": ["position", "battery"]})
        report["partial"] = partial
        check(not partial["is_error"] and set(partial["value"]["readings"]) == {"battery"}
              and set(partial["value"]["errors"]) == {"position"}, partial)
        check("timeout:" in partial["value"]["errors"]["position"], partial)
        total = await call(session, "get_vehicle_telemetry", {"fields": ["position", "velocity"]})
        report["total_failure"] = total
        check(total["is_error"] and "telemetry_unavailable:" in total["value"], total)
        check(total["elapsed_s"] < 13 and partial["elapsed_s"] < 13, (partial, total))
        cancelled = asyncio.create_task(call(session, "get_vehicle_telemetry",
                                             {"fields": ["position"]}))
        await asyncio.sleep(.5)
        cancelled.cancel()
        with suppress(asyncio.CancelledError):
            await cancelled
        await asyncio.sleep(.2)
        after_cancel = await call(session, "get_vehicle_telemetry", {"fields": ["battery"]})
        report["after_cancellation"] = after_cancel
        check(not after_cancel["is_error"] and not after_cancel["value"]["errors"], after_cancel)
        pending = asyncio.create_task(call(session, "get_vehicle_telemetry",
                                           {"fields": ["position", "battery"]}))
        await asyncio.sleep(.5)
        router.blackout = True
        started = time.monotonic()
        report["disconnect"] = await wait_state(session, "disconnected")
        report["disconnect_elapsed_s"] = round(time.monotonic() - started, 3)
        interrupted = await pending
        report["interrupted_batch"] = interrupted
        check(interrupted["is_error"] and any(reason in interrupted["value"] for reason in
              ["connection_changed:", "invalid_target:", "not_connected:"]), interrupted)
        ping = await call(session, "ping")
        report["ping_disconnected"] = ping
        check(not ping["is_error"] and ping["value"] == "pong", ping)
        unavailable = await call(session, "get_vehicle_information")
        report["information_disconnected"] = unavailable
        check(unavailable["is_error"] and "not_connected:" in unavailable["value"], unavailable)
        router.blocked.clear()
        router.blackout = False
        report["recovery"] = await wait_state(session, "connected")
        recovered = await call(session, "get_vehicle_telemetry", {"fields": FIELDS})
        report["recovered_telemetry"] = recovered
        check(not recovered["is_error"] and not recovered["value"]["errors"], recovered)

    router.blocked = {"AUTOPILOT_VERSION", "GPS_RAW_INT", "GPS2_RAW"}
    async with session_for(args.output, config, "missing-info-gps") as session:
        await wait_state(session, "connected")
        info = await call(session, "get_vehicle_information")
        report["unavailable_information"] = info
        check(info["is_error"] and "information_unavailable:" in info["value"], info)
        gps = await call(session, "get_vehicle_telemetry", {"fields": ["gps", "battery"]})
        report["missing_gps"] = gps
        check(not gps["is_error"] and set(gps["value"]["readings"]) == {"battery"}
              and set(gps["value"]["errors"]) == {"gps"}, gps)
        check((await call(session, "ping"))["value"] == "pong", "MCP unresponsive")
    router.blocked.clear()


async def main(args, report):
    loop = asyncio.get_running_loop()
    mamba_port = free_port()
    router = Router(mamba_port)
    transport, _ = await loop.create_datagram_endpoint(
        lambda: router, local_addr=("127.0.0.1", 0))
    router_port = transport.get_extra_info("sockname")[1]
    config = args.output / "vehicle.toml"
    config.write_text(f'[vehicle]\nconnection_url = "udpin://127.0.0.1:{mamba_port}"\nsystem_id = 1\n')
    defaults = args.ardupilot / "Tools/autotest/default_params/copter.parm"
    command = [str(args.binary), "--model", "quad", "--home", "40,-74,125,0",
               "--defaults", str(defaults), "--sysid", "1", "--instance", "31",
               "--serial0", f"udpclient:127.0.0.1:{router_port}"]
    report["simulator_command"] = command
    report["endpoints"] = {"router_port": router_port, "mamba_port": mamba_port}
    process = None
    try:
        with (args.output / "sitl.log").open("w") as log:
            process = await asyncio.create_subprocess_exec(
                *command, cwd=args.output, stdout=log, stderr=asyncio.subprocess.STDOUT)
            await router.wait_for("HEARTBEAT")
            check(process.returncode is None, "SITL exited during startup")
            # A bare SITL serial link has no GCS stream requests. Do what
            # MAVProxy normally does: request simulator telemetry at 4 Hz.
            encoder = mavlink.MAVLink(None, srcSystem=255, srcComponent=190)
            request = encoder.request_data_stream_encode(
                1, 1, mavlink.MAV_DATA_STREAM_ALL, 4, 1)
            transport.sendto(request.pack(encoder), router.simulator_address)
            async with asyncio.timeout(240):
                await validate(args, report, router, config)
    finally:
        transport.close()
        if process is not None:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), 10)
                except TimeoutError:
                    process.kill()
                    await process.wait()
            report["simulator_exit_code"] = process.returncode
        with (args.output / "wire-observations.jsonl").open("w") as wire:
            for observation in router.observations:
                wire.write(json.dumps(observation) + "\n")
        report["wire_observation_count"] = len(router.observations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ardupilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory for isolated EEPROM, logs and JSON evidence")
    args = parser.parse_args()
    args.ardupilot = args.ardupilot.resolve()
    args.binary = args.ardupilot / "build/sitl/bin/arducopter"
    check(args.binary.is_file(), f"Build ArduCopter SITL first: {args.binary}")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"started_at": utc_now(), "platform": platform.platform(),
              "python": sys.version, "versions": {name: version(name) for name in
                  ["fastmcp", "mavsdk", "mcp", "pymavlink"]},
              "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
              "defaults_sha256": hashlib.sha256((args.ardupilot /
                  "Tools/autotest/default_params/copter.parm").read_bytes()).hexdigest(),
              "ardupilot_source_revision": subprocess.check_output(
                  ["git", "-C", str(args.ardupilot), "rev-parse", "HEAD"], text=True).strip(),
              "mamba_base_revision": subprocess.check_output(
                  ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
              "passed": False}
    try:
        asyncio.run(main(args, report))
        report["passed"] = True
    except BaseException as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at"] = utc_now()
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
