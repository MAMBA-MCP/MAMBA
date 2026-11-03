"""Read-only native MAVSDK information and telemetry (MAMBA-26 / MAMBA-27)."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import logging
import math
from typing import Annotated, Generic, Literal, TypeVar

from mavsdk.asyncio.plugins.info import InfoAsync
from mavsdk.asyncio.plugins.telemetry import TelemetryAsync
from mavsdk.asyncio.system import System
from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, model_serializer

if __package__:
    from .connection import VehicleConnection, utc_now
else:
    from connection import VehicleConnection, utc_now

REQUEST_TIMEOUT = 10.0
LOGGER = logging.getLogger("mamba.vehicle_data")
Data = TypeVar("Data", bound=BaseModel)


class Reading(BaseModel, Generic[Data]):
    system_id: int
    received_at: str
    data: Data


class IdentificationData(BaseModel):
    hardware_uid: str | None = None
    legacy_uid: int | None = None


class VersionData(BaseModel):
    flight_sw_major: int | None = None
    flight_sw_minor: int | None = None
    flight_sw_patch: int | None = None
    flight_sw_vendor_major: int | None = None
    flight_sw_vendor_minor: int | None = None
    flight_sw_vendor_patch: int | None = None
    os_sw_major: int | None = None
    os_sw_minor: int | None = None
    os_sw_patch: int | None = None
    flight_sw_git_hash: str | None = None
    os_sw_git_hash: str | None = None
    flight_sw_version_type: str | None = None


class InformationData(BaseModel):
    identification: IdentificationData | None = None
    version: VersionData | None = None
    errors: dict[str, str]


class PositionData(BaseModel):
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    absolute_altitude_m: float | None = None
    relative_altitude_m: float | None = None


class VelocityData(BaseModel):
    north_m_s: float | None = None
    east_m_s: float | None = None
    down_m_s: float | None = None


class BatteryData(BaseModel):
    id: int | None = None
    temperature_degc: float | None = None
    voltage_v: float | None = None
    current_battery_a: float | None = None
    capacity_consumed_ah: float | None = None
    remaining_percent: float | None = None
    time_remaining_s: float | None = None
    battery_function: str | None = None


class GpsData(BaseModel):
    num_satellites: int | None = None
    fix_type: str | None = None


class HealthData(BaseModel):
    is_gyrometer_calibration_ok: bool | None = None
    is_accelerometer_calibration_ok: bool | None = None
    is_magnetometer_calibration_ok: bool | None = None
    is_local_position_ok: bool | None = None
    is_global_position_ok: bool | None = None
    is_home_position_ok: bool | None = None
    is_armable: bool | None = None


TelemetryField = Literal["position", "velocity", "battery", "gps", "health"]


def unique_fields(fields: list[TelemetryField]) -> list[TelemetryField]:
    if len(fields) != len(set(fields)):
        raise ValueError("fields must contain unique telemetry categories")
    return fields


TelemetryFields = Annotated[
    list[TelemetryField],
    Field(min_length=1, max_length=5, json_schema_extra={"uniqueItems": True}),
    AfterValidator(unique_fields),
]
TELEMETRY_FIELDS_ADAPTER = TypeAdapter(TelemetryFields)


class TelemetrySample(BaseModel, Generic[Data]):
    received_at: str
    data: Data


class TelemetryReadings(BaseModel):
    position: TelemetrySample[PositionData] | None = None
    velocity: TelemetrySample[VelocityData] | None = None
    battery: TelemetrySample[BatteryData] | None = None
    gps: TelemetrySample[GpsData] | None = None
    health: TelemetrySample[HealthData] | None = None

    @model_serializer(mode="wrap")
    def serialize_readings(self, handler):
        # Omit absent categories without dropping unknown measurements inside them.
        return {name: value for name, value in handler(self).items()
                if getattr(self, name) is not None}


class TelemetryResult(BaseModel):
    system_id: int
    readings: TelemetryReadings
    errors: dict[TelemetryField, str]


class RetrievalError(Exception):
    """A controlled availability, timeout, or SDK retrieval failure."""


def sdk_data(raw: object, model: type[Data]) -> Data:
    if raw is None:
        raise RetrievalError("missing_reading: MAVSDK returned no data")
    values = {}
    for name in model.model_fields:
        value = getattr(raw, name, None)
        if isinstance(value, Enum):
            value = value.name
        elif isinstance(value, float) and not math.isfinite(value):
            value = None
        values[name] = value
    return model.model_validate(values)


@dataclass
class InformationOperation:
    tasks: dict[str, asyncio.Task]
    completion: asyncio.Task | None = None


class VehicleData:
    """Own on-demand requests and drain native work before SDK destruction."""

    def __init__(self, connection: VehicleConnection):
        self.connection = connection
        self._closed = False
        self._calls: set[asyncio.Task] = set()
        self._information: dict[int, InformationOperation] = {}
        self._native_tasks: set[asyncio.Task] = set()

    async def __aenter__(self) -> "VehicleData":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        self._closed = True
        # End subscription readers first; information workers remain shielded.
        calls = list(self._calls)
        for task in calls:
            task.cancel()
        await asyncio.gather(*calls, return_exceptions=True)
        await asyncio.gather(*list(self._native_tasks), return_exceptions=True)

    @asynccontextmanager
    async def _request(self, name: str) -> AsyncIterator[None]:
        if self._closed:
            raise RetrievalError("unavailable: vehicle data service is stopping")
        task = asyncio.current_task()
        self._calls.add(task)
        started = asyncio.get_running_loop().time()
        outcome = "ok"
        try:
            yield
        except asyncio.CancelledError:
            outcome = "cancelled"
            raise
        except RetrievalError as exc:
            outcome = str(exc)
            raise
        except Exception as exc:
            outcome = f"sdk_error: {name}: {exc}"
            raise RetrievalError(outcome) from exc
        finally:
            self._calls.discard(task)
            LOGGER.info("Vehicle %s %s: %s (%.1f ms)",
                        self.connection.status.system_id, name, outcome,
                        (asyncio.get_running_loop().time() - started) * 1000)

    async def _target(self) -> tuple[System, int]:
        connection = self.connection
        system = connection.system
        generation = connection.generation
        if (connection.config is None or connection.status.state != "connected"
                or system is None):
            raise RetrievalError("not_connected: configured vehicle is unavailable")
        await self._validate(system, generation)
        return system, generation

    async def _validate(self, system: System, generation: int) -> None:
        connection = self.connection
        if (self._closed or connection.config is None
                or connection.generation != generation
                or connection.status.state != "connected"
                or connection.system is None):
            raise RetrievalError("connection_changed: vehicle connection is no longer valid")
        if (connection.status.system_id != connection.config.system_id
                or await system.get_system_id() != connection.config.system_id
                or not await system.is_connected()
                or not await system.has_autopilot()):
            raise RetrievalError("invalid_target: configured autopilot is not connected")
        # Awaited checks must not permit a disconnect/reconnect to go unnoticed.
        if connection.generation != generation or self._closed:
            raise RetrievalError("connection_changed: vehicle reconnected during retrieval")

    async def _telemetry(self, topic: str, model: type[Data]) -> Reading[Data]:
        async with self._request(topic):
            try:
                async with asyncio.timeout(REQUEST_TIMEOUT):
                    system, generation = await self._target()
                    plugin = TelemetryAsync(system)
                    stream = None
                    try:
                        stream = getattr(plugin, f"subscribe_{topic}")()
                        raw = await anext(stream)
                        received_at = utc_now()
                        data = sdk_data(raw, model)
                        await self._validate(system, generation)
                        return Reading[model](
                            system_id=self.connection.config.system_id,
                            received_at=received_at, data=data,
                        )
                    finally:
                        try:
                            if stream is not None:
                                await stream.aclose()
                        finally:
                            plugin.destroy()
            except TimeoutError as exc:
                raise RetrievalError(f"timeout: no {topic} reading within {REQUEST_TIMEOUT:g}s") from exc
            except StopAsyncIteration as exc:
                raise RetrievalError(f"missing_reading: {topic} stream ended without data") from exc

    async def position(self) -> Reading[PositionData]:
        return await self._telemetry("position", PositionData)

    async def velocity(self) -> Reading[VelocityData]:
        return await self._telemetry("velocity_ned", VelocityData)

    async def battery(self) -> Reading[BatteryData]:
        return await self._telemetry("battery", BatteryData)

    async def gps(self) -> Reading[GpsData]:
        return await self._telemetry("gps_info", GpsData)

    async def health(self) -> Reading[HealthData]:
        return await self._telemetry("health", HealthData)

    async def telemetry(self, fields: TelemetryFields) -> TelemetryResult:
        fields = TELEMETRY_FIELDS_ADAPTER.validate_python(fields, strict=True)
        async with self._request("telemetry"):
            loop = asyncio.get_running_loop()
            deadline = loop.time() + REQUEST_TIMEOUT
            try:
                async with asyncio.timeout_at(deadline):
                    system, generation = await self._target()
            except TimeoutError as exc:
                raise RetrievalError("timeout: telemetry target validation timed out") from exc

            async def read(field: TelemetryField):
                try:
                    async with asyncio.timeout_at(deadline):
                        return await getattr(self, field)()
                except TimeoutError as exc:
                    raise RetrievalError(
                        f"timeout: no {field} reading within {REQUEST_TIMEOUT:g}s"
                    ) from exc

            tasks = {field: asyncio.create_task(read(field)) for field in fields}
            try:
                _, pending = await asyncio.wait(
                    tasks.values(), timeout=max(0, deadline - loop.time())
                )
                for task in pending:
                    task.cancel()
                outcomes = await asyncio.gather(*tasks.values(), return_exceptions=True)
            finally:
                for task in tasks.values():
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Reject every earlier reading if the batch crossed a connection session.
            await self._validate(system, generation)
            readings = {}
            errors = {}
            for (field, task), outcome in zip(tasks.items(), outcomes):
                if (isinstance(outcome, RetrievalError)
                        and str(outcome).partition(":")[0] in {
                            "not_connected", "invalid_target", "connection_changed", "unavailable"
                        }):
                    raise RetrievalError(str(outcome))
                if task in pending or isinstance(outcome, asyncio.CancelledError):
                    errors[field] = f"timeout: no {field} reading within {REQUEST_TIMEOUT:g}s"
                elif isinstance(outcome, BaseException):
                    reason = str(outcome)
                    errors[field] = reason if isinstance(outcome, RetrievalError) else f"sdk_error: {reason}"
                else:
                    if outcome.system_id != self.connection.config.system_id:
                        raise RetrievalError("invalid_target: telemetry categories have different targets")
                    readings[field] = {"received_at": outcome.received_at, "data": outcome.data}
            if not readings:
                raise RetrievalError("telemetry_unavailable: " + "; ".join(
                    f"{field}: {reason}" for field, reason in errors.items()
                ))
            return TelemetryResult(
                system_id=self.connection.config.system_id,
                readings=TelemetryReadings(**readings), errors=errors,
            )

    async def _information_part(self, method, model):
        raw = await method()
        return sdk_data(raw, model), utc_now()

    def _start_information(self, system: System, generation: int) -> InformationOperation:
        operation = self._information.get(generation)
        if operation is not None:
            return operation
        plugin = InfoAsync(system)
        operation = InformationOperation(tasks={
            "identification": asyncio.create_task(self._information_part(
                plugin.get_identification, IdentificationData)),
            "version": asyncio.create_task(self._information_part(
                plugin.get_version, VersionData)),
        })
        self._information[generation] = operation

        async def finish():
            try:
                await asyncio.gather(*operation.tasks.values(), return_exceptions=True)
            finally:
                try:
                    plugin.destroy()
                finally:
                    self._information.pop(generation, None)

        operation.completion = asyncio.create_task(finish())
        self._native_tasks.add(operation.completion)
        operation.completion.add_done_callback(self._native_finished)
        return operation

    def _native_finished(self, task: asyncio.Task) -> None:
        self._native_tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            LOGGER.error("Native information cleanup failed: %s", task.exception())

    async def information(self) -> Reading[InformationData]:
        async with self._request("information"):
            operation = None
            try:
                async with asyncio.timeout(REQUEST_TIMEOUT):
                    system, generation = await self._target()
                    operation = self._start_information(system, generation)
                    await asyncio.shield(operation.completion)
            except TimeoutError as exc:
                if operation is None:
                    raise RetrievalError("timeout: vehicle information request timed out") from exc
            errors = {}
            sections = {}
            received = []
            for name, task in operation.tasks.items():
                if not task.done():
                    errors[name] = f"timeout: no {name} within {REQUEST_TIMEOUT:g}s"
                elif task.cancelled():
                    errors[name] = f"cancelled: {name} retrieval interrupted"
                elif task.exception() is not None:
                    errors[name] = f"sdk_error: {task.exception()}"
                else:
                    sections[name], timestamp = task.result()
                    received.append(timestamp)
            await self._validate(system, generation)
            if not sections:
                raise RetrievalError("information_unavailable: " + "; ".join(
                    f"{name}: {reason}" for name, reason in errors.items()
                ))
            return Reading[InformationData](
                system_id=self.connection.config.system_id,
                received_at=max(received),
                data=InformationData(**sections, errors=errors),
            )
