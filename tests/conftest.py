"""Controlled native SDK substitutes for MAMBA-26/27 retrieval tests."""

import asyncio
from collections import Counter
from types import SimpleNamespace

import pytest
from mavsdk.plugins.info import Identification, Version
from mavsdk.plugins.telemetry import Battery, BatteryFunction, FixType, GpsInfo, Health, Position, VelocityNed

from mamba.connection import VehicleConfig, VehicleConnection
from mamba import vehicle_data


class FakeVehicle:
    def __init__(self):
        self.connected = True
        self.system_id = 1
        self.autopilot = True

    async def get_system_id(self):
        return self.system_id

    async def is_connected(self):
        return self.connected

    async def has_autopilot(self):
        return self.autopilot


@pytest.fixture
def data_sdk(monkeypatch):
    target = FakeVehicle()
    connection = VehicleConnection(VehicleConfig('udpin://127.0.0.1:14540', 1))
    connection.system = target
    connection.set_state('connected', 'test vehicle')
    harness = SimpleNamespace(
        connection=connection, target=target, telemetry_plugins=[], info_plugins=[],
        reads=Counter(), gates={}, errors={}, empty=set(),
        values={
            'position': Position(40.0, -74.0, 125.5, 0.0),
            'velocity_ned': VelocityNed(0.0, -2.0, 3.0),
            'battery': Battery(id=0, voltage_v=12.5, current_battery_a=0.0,
                               remaining_percent=75.0, temperature_degc=float('nan'),
                               time_remaining_s=float('inf'),
                               battery_function=BatteryFunction.PROPULSION),
            'gps_info': GpsInfo(0, FixType.NO_FIX),
            'health': Health(False, True, False, False, False, True, False),
            'identification': Identification('hardware-1', 1234567890123456789),
            'version': Version(flight_sw_major=4, flight_sw_minor=6, flight_sw_patch=0,
                               flight_sw_version_type=Version.FlightSoftwareVersionType.RELEASE),
        },
    )

    async def receive(name):
        harness.reads[name] += 1
        gate = harness.gates.get(name)
        if gate is not None:
            await gate.wait()
        if name in harness.errors:
            raise harness.errors[name]
        return harness.values[name]

    class FakeTelemetry:
        def __init__(self, system):
            assert system is target
            self.active = 0
            self.closed = []
            self.destroyed = False
            harness.telemetry_plugins.append(self)

        def __getattr__(self, name):
            if name.startswith('subscribe_'):
                return lambda: self.stream(name.removeprefix('subscribe_'))
            raise AttributeError(name)

        async def stream(self, topic):
            self.active += 1
            try:
                if topic in harness.empty:
                    return
                yield await receive(topic)
            finally:
                self.active -= 1
                self.closed.append(topic)

        def destroy(self):
            assert self.active == 0, 'subscription must close before plugin destruction'
            self.destroyed = True

    class FakeInfo:
        def __init__(self, system):
            assert system is target
            self.active = 0
            self.destroyed = False
            harness.info_plugins.append(self)

        async def get_identification(self):
            return await self.read('identification')

        async def get_version(self):
            return await self.read('version')

        async def read(self, name):
            self.active += 1
            try:
                return await receive(name)
            finally:
                self.active -= 1

        def destroy(self):
            assert self.active == 0, 'native operations must finish before destruction'
            self.destroyed = True

    monkeypatch.setattr(vehicle_data, 'TelemetryAsync', FakeTelemetry)
    monkeypatch.setattr(vehicle_data, 'InfoAsync', FakeInfo)
    return harness
