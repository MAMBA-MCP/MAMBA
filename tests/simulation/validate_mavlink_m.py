"""Opt-in MAMBA-28/29 native XML and own-position wire acceptance.

Launches its own disarmed SITL; never connects to the operator's SITL or hardware.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
import hashlib
import importlib.util
from importlib.metadata import version
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mavsdk.asyncio.plugins.mavlink_direct import MavlinkDirectAsync, MavlinkDirectError
from mavsdk.asyncio import Configuration, Mavsdk
from pymavlink.generator import mavgen

from mamba.connection import VehicleConnection, VehicleConfig, sdk_log, log_subscribe, log_unsubscribe
from mamba.participant import ParticipantPosition, participant_xml, pinned_dialect
from mamba.vehicle_data import VehicleData
from validate_read_only import Router, check, free_port, utc_now


@asynccontextmanager
async def simulation_connection(config):
    # Native send_message uses the SDK configuration, ignoring per-message
    # source overrides. Use a companion component on the simulated vehicle.
    connection = VehicleConnection(VehicleConfig.load(config))
    connection.sdk = Mavsdk(Configuration.create_manual(1, 191, False))
    log_subscribe(sdk_log)
    task = asyncio.create_task(connection.run())
    try:
        yield connection
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        log_unsubscribe()


def independent_binding(output):
    path = output / "participant.xml"
    path.write_text(participant_xml())
    target = output / "participant_wire.py"
    options = mavgen.Opts(str(target), wire_protocol="2.0", language="Python3", validate=False)
    check(mavgen.mavgen(options, [str(path)]), "pymavlink generation failed")
    spec = importlib.util.spec_from_file_location("participant_wire", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PositionRouter(Router):
    def __init__(self, mamba_port, binding):
        super().__init__(mamba_port)
        self.binding = binding
        self.decoder = binding.MAVLink(None)
        self.decoder.robust_parsing = True
        self.positions = []

    def datagram_received(self, data, address):
        if address == self.mamba_address:
            reports = [m for m in self.decoder.parse_buffer(data) or []
                       if m.get_type() == "PARTICIPANT_POSITION"]
            if reports:
                for message in reports:
                    self.positions.append({"received_at": utc_now(),
                        "system_id": message.get_srcSystem(),
                        "component_id": message.get_srcComponent(),
                        "wire_hex": bytes(message.get_msgbuf()).hex(),
                        "crc": message.get_crc(), "fields": message.to_dict()})
                # Local sink only: never route generated reports to the autopilot.
                return
        super().datagram_received(data, address)

    async def next_report(self, previous):
        async with asyncio.timeout(5):
            while len(self.positions) <= previous:
                await asyncio.sleep(.01)
        return self.positions[-1]


def compare_fields(expected, actual):
    for key, value in expected.items():
        found = actual[key]
        if value is None:
            check(isinstance(found, float) and math.isnan(found), f"{key}: unknown became {found}")
        elif isinstance(value, float):
            check(math.isclose(value, found, rel_tol=1e-6, abs_tol=1e-5), (key, value, found))
        else:
            check(value == found, (key, value, found))


async def run(args, report):
    binding = independent_binding(args.output)
    report["message_id"] = binding.MAVLINK_MSG_ID_PARTICIPANT_POSITION
    report["crc_extra"] = binding.MAVLink_participant_position_message.crc_extra
    loop = asyncio.get_running_loop()
    mamba_port = free_port()
    router = PositionRouter(mamba_port, binding)
    transport, _ = await loop.create_datagram_endpoint(lambda: router, local_addr=("127.0.0.1", 0))
    router_port = transport.get_extra_info("sockname")[1]
    config = args.output / "vehicle.toml"
    config.write_text(f'[vehicle]\nconnection_url = "udpin://127.0.0.1:{mamba_port}"\nsystem_id = 1\n')
    command = [str(args.binary), "--model", "quad", "--home", "40,-74,125,0",
               "--defaults", str(args.ardupilot / "Tools/autotest/default_params/copter.parm"),
               "--sysid", "1", "--instance", "32", "--serial0",
               f"udpclient:127.0.0.1:{router_port}"]
    report["simulator_command"] = command
    process = None
    try:
        with (args.output / "sitl.log").open("w") as log:
            process = await asyncio.create_subprocess_exec(*command, cwd=args.output,
                stdout=log, stderr=asyncio.subprocess.STDOUT)
            await router.wait_for("HEARTBEAT")
            from pymavlink.dialects.v20 import common
            encoder = common.MAVLink(None, srcSystem=255, srcComponent=190)
            transport.sendto(encoder.request_data_stream_encode(
                1, 1, common.MAV_DATA_STREAM_ALL, 4, 1).pack(encoder), router.simulator_address)
            async with simulation_connection(config) as connection:
                async with asyncio.timeout(30):
                    while connection.status.state != "connected":
                        await asyncio.sleep(.1)
                system, generation = connection.system, connection.generation
                plugin = MavlinkDirectAsync(system)
                try:
                    async with VehicleData(connection) as data:
                        async with asyncio.timeout(60):
                            while True:
                                telemetry = await data.telemetry(["position", "velocity", "health"])
                                health = telemetry.readings.health
                                if (health and health.data.is_global_position_ok
                                        and health.data.is_home_position_ok):
                                    break
                                await asyncio.sleep(1)
                        report["telemetry_source"] = telemetry.model_dump(mode="json")
                        sample = ParticipantPosition.from_telemetry(telemetry,
                            time_usec=time.time_ns() // 1000, callsign="MAMBA-SITL")
                        message = sample.to_message(component_id=191)
                        try:
                            await plugin.send_message(message)
                        except MavlinkDirectError as exc:
                            report["before_xml"] = exc.result.name
                        else:
                            raise AssertionError("Custom message unexpectedly available before XML load")
                        try:
                            await plugin.load_custom_xml("<mavlink><bad>")
                        except MavlinkDirectError as exc:
                            report["malformed_xml"] = exc.result.name
                        else:
                            raise AssertionError("Malformed XML was accepted")
                        await plugin.load_custom_xml(pinned_dialect())
                        report["full_xml_load"] = "success (includes not needed for custom fields)"
                        await plugin.load_custom_xml(participant_xml())
                        report["scoped_xml_load"] = "success"
                        # Validate session immediately before publishing to the local sink.
                        await data._validate(system, generation)
                        previous = len(router.positions)
                        await plugin.send_message(message)
                        observed = await router.next_report(previous)
                        report["own_position"] = observed
                        report["own_position_expected"] = sample.model_dump(mode="json")
                        raw_position = router.nearest("GLOBAL_POSITION_INT",
                            telemetry.readings.position.received_at)
                        report["independent_sitl_source"] = raw_position
                        check(abs(sample.lat - raw_position["message"]["lat"]) <= 10
                              and abs(sample.lon - raw_position["message"]["lon"]) <= 10,
                              "Position scaling differs from raw SITL coordinates")
                        check(abs(sample.lat / 1e7 - 40) < .001
                              and abs(sample.lon / 1e7 + 74) < .001,
                              "SITL position was not initialized at the configured home")
                        check(observed["system_id"] == sample.origin_sysid == 1
                              and observed["component_id"] == 191, observed)
                        compare_fields(sample.model_dump(), observed["fields"])

                        # Nonzero axes, string boundaries and uint64 verify protocol details
                        # separately from the stationary SITL sample.
                        boundaries = sample.model_copy(update={"time_usec": 2**64 - 1,
                            "lat": -900_000_000, "lon": 1_800_000_000, "alt": -12.5,
                            "vx": 1.25, "vy": -2.5, "vz": .75, "course": 359.5,
                            "callsign": "S" * 49, "external_track_number": "T" * 19,
                            "external_track_type": 3})
                        previous = len(router.positions)
                        await plugin.send_message(boundaries.to_message(component_id=191))
                        boundary_wire = await router.next_report(previous)
                        compare_fields(boundaries.model_dump(), boundary_wire["fields"])
                        report["boundary_roundtrip"] = boundary_wire

                        # Do not assume the native API rejects semantic overflow/unknown keys.
                        probes = {}
                        for name, patch in [("unknown_field", {"unexpected": 1}),
                                            ("uint8_overflow", {"origin_sysid": 256})]:
                            raw = sample.to_message(component_id=191)
                            raw.fields_json = json.dumps(sample.model_dump() | patch)
                            previous = len(router.positions)
                            try:
                                await plugin.send_message(raw)
                            except MavlinkDirectError as exc:
                                probes[name] = {"result": exc.result.name}
                            else:
                                wire = await router.next_report(previous)
                                probes[name] = {"result": "accepted_by_sdk", "wire": wire}
                        report["native_validation_probes"] = probes
                        raw = sample.to_message(component_id=88)
                        raw.system_id = 99
                        previous = len(router.positions)
                        await plugin.send_message(raw)
                        source_probe = await router.next_report(previous)
                        report["source_override_probe"] = source_probe
                        check((source_probe["system_id"], source_probe["component_id"]) == (1, 191),
                              "Configured sender identity behavior changed; review mapping")

                        # Independently encoded incoming report, including IEEE NaN unknowns.
                        reverse_fields = sample.model_dump() | {"time_usec": 2**63 + 123,
                            "lat": sample.lat + 1, "course": 123.25, "vx": -1.5,
                            "alt": None, "vy": None}
                        encoder = binding.MAVLink(None, srcSystem=1, srcComponent=192)
                        kwargs = reverse_fields | {"callsign": sample.callsign.encode("ascii"),
                            "external_track_number": b""}
                        kwargs = {k: float("nan") if v is None else v for k, v in kwargs.items()}
                        packet = encoder.participant_position_encode(**kwargs).pack(encoder)
                        stream = plugin.subscribe_message("PARTICIPANT_POSITION")
                        reader = asyncio.create_task(anext(stream))
                        await asyncio.sleep(.1)
                        try:
                            broken = bytearray(packet)
                            broken[-1] ^= 1
                            transport.sendto(bytes(broken), router.mamba_address)
                            await asyncio.sleep(.3)
                            check(not reader.done(), "Invalid CRC was delivered to native subscriber")
                            report["bad_crc_rejected"] = True
                            transport.sendto(packet, router.mamba_address)
                            incoming = await asyncio.wait_for(reader, 5)
                            received = json.loads(incoming.fields_json)
                            # SDK JSON uses null for unknown floating point values.
                            for key, expected in reverse_fields.items():
                                actual = received[key]
                                if isinstance(expected, float):
                                    check(math.isclose(actual, expected, abs_tol=1e-5), (key,actual,expected))
                                else:
                                    check(actual == expected, (key,actual,expected))
                            check(incoming.system_id == 1 and incoming.component_id == 192,
                                  "Incoming source identity was not retained")
                            report["reverse_roundtrip"] = {"system_id": incoming.system_id,
                                "component_id": incoming.component_id, "fields": received}
                        finally:
                            reader.cancel()
                            await asyncio.gather(reader, return_exceptions=True)
                            await stream.aclose()
                        check(connection.generation == generation, "Connection changed during scenario")
                        report["connection_persisted"] = connection.status.state == "connected"
                finally:
                    plugin.destroy()
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
        report["wire_position_count"] = len(router.positions)


def finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: finite_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite_json(v) for v in value]
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ardupilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.ardupilot = args.ardupilot.resolve()
    args.binary = args.ardupilot / "build/sitl/bin/arducopter"
    check(args.binary.is_file(), f"Missing SITL binary: {args.binary}")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"started_at": utc_now(), "passed": False,
        "versions": {name: version(name) for name in ["mavsdk", "pymavlink", "pydantic"]},
        "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        "ardupilot_source_revision": subprocess.check_output(
            ["git", "-C", str(args.ardupilot), "rev-parse", "HEAD"], text=True).strip(),
        "mamba_base_revision": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()}
    try:
        asyncio.run(asyncio.wait_for(run(args, report), 120))
        report["passed"] = True
    except BaseException as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at"] = utc_now()
        (args.output / "report.json").write_text(json.dumps(finite_json(report), indent=2, allow_nan=False) + "\n")
        print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
