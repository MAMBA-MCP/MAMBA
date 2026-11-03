"""F2/A02, F3/A03: MAMBA-26/27 reads, isolation, deadlines, and cleanup."""

import asyncio
from datetime import datetime

import pytest

from mamba import vehicle_data
from mamba.vehicle_data import RetrievalError, VehicleData


async def wait_until(predicate):
    async with asyncio.timeout(1):
        while not predicate():
            await asyncio.sleep(.001)


@pytest.mark.parametrize('method, field, expected', [
    ('position', 'latitude_deg', 40.0),
    ('velocity', 'down_m_s', 3.0),
    ('battery', 'remaining_percent', 75.0),
    ('gps', 'fix_type', 'NO_FIX'),
    ('health', 'is_armable', False),
])
def test_telemetry_values_units_and_cleanup(data_sdk, method, field, expected):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            reading = await getattr(service, method)()
            assert reading.system_id == 1
            assert datetime.fromisoformat(reading.received_at).utcoffset().total_seconds() == 0
            assert getattr(reading.data, field) == expected
            if method == 'position':
                assert reading.data.relative_altitude_m == 0.0
            if method == 'battery':
                assert reading.data.current_battery_a == 0.0
                assert reading.data.id == 0
                assert reading.data.temperature_degc is None
                assert reading.data.time_remaining_s is None
                assert reading.data.battery_function == 'PROPULSION'
                assert 'NaN' not in reading.model_dump_json()
            if method == 'gps':
                assert reading.data.num_satellites == 0
            assert data_sdk.telemetry_plugins[-1].destroyed
    asyncio.run(scenario())


def test_telemetry_has_no_application_cache(data_sdk):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            first = await service.position()
            data_sdk.values['position'].latitude_deg = 41.0
            second = await service.position()
            assert first.data.latitude_deg == 40.0
            assert second.data.latitude_deg == 41.0
            assert data_sdk.reads['position'] == 2
    asyncio.run(scenario())


@pytest.mark.parametrize('kind', ['timeout', 'error', 'empty', 'none'])
def test_telemetry_failure_cleanup(data_sdk, monkeypatch, kind):
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .02)

    async def scenario():
        if kind == 'timeout':
            data_sdk.gates['position'] = asyncio.Event()
        elif kind == 'error':
            data_sdk.errors['position'] = RuntimeError('SDK unavailable')
        elif kind == 'empty':
            data_sdk.empty.add('position')
        else:
            data_sdk.values['position'] = None
        async with VehicleData(data_sdk.connection) as service:
            started = asyncio.get_running_loop().time()
            with pytest.raises(RetrievalError, match={
                'timeout': 'timeout:', 'error': 'sdk_error:',
                'empty': 'missing_reading:', 'none': 'missing_reading:',
            }[kind]):
                await service.position()
            assert asyncio.get_running_loop().time() - started < 1
            assert data_sdk.telemetry_plugins[-1].destroyed
    asyncio.run(scenario())


def test_telemetry_cancellation_and_service_shutdown(data_sdk):
    async def scenario():
        data_sdk.gates['position'] = asyncio.Event()
        async with VehicleData(data_sdk.connection) as service:
            request = asyncio.create_task(service.position())
            await wait_until(lambda: data_sdk.reads['position'] == 1)
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
            assert data_sdk.telemetry_plugins[-1].destroyed
            remaining = asyncio.create_task(service.position())
            await wait_until(lambda: data_sdk.reads['position'] == 2)
        assert remaining.cancelled()
        assert all(p.destroyed for p in data_sdk.telemetry_plugins)
        with pytest.raises(RetrievalError, match='stopping'):
            await service.position()
    asyncio.run(scenario())


@pytest.mark.parametrize('state', ['unconfigured', 'connecting', 'disconnected', 'error'])
def test_reads_require_connected_target(data_sdk, state):
    async def scenario():
        data_sdk.connection.set_state(state, 'not available')
        async with VehicleData(data_sdk.connection) as service:
            for method in ['position', 'velocity', 'battery', 'gps', 'health', 'information']:
                with pytest.raises(RetrievalError, match='not_connected'):
                    await getattr(service, method)()
        assert not data_sdk.telemetry_plugins and not data_sdk.info_plugins
    asyncio.run(scenario())


@pytest.mark.parametrize('fault', ['id', 'disconnected', 'not_autopilot', 'inconsistent_id'])
def test_invalid_target_is_rejected(data_sdk, fault):
    async def scenario():
        if fault == 'id':
            data_sdk.target.system_id = 2
        elif fault == 'disconnected':
            data_sdk.target.connected = False
        elif fault == 'not_autopilot':
            data_sdk.target.autopilot = False
        else:
            data_sdk.connection.status.system_id = 2
        async with VehicleData(data_sdk.connection) as service:
            with pytest.raises(RetrievalError, match='invalid_target'):
                await service.battery()
        assert not data_sdk.telemetry_plugins
    asyncio.run(scenario())


@pytest.mark.parametrize('reconnect', [False, True])
def test_rejects_read_after_disconnect_or_reconnect(data_sdk, reconnect):
    async def scenario():
        gate = data_sdk.gates['position'] = asyncio.Event()
        async with VehicleData(data_sdk.connection) as service:
            request = asyncio.create_task(service.position())
            await wait_until(lambda: data_sdk.reads['position'] == 1)
            old_generation = data_sdk.connection.generation
            data_sdk.connection.set_state('disconnected', 'link lost')
            if reconnect:
                data_sdk.connection.set_state('connected', 'link restored')
            assert data_sdk.connection.generation != old_generation
            gate.set()
            with pytest.raises(RetrievalError, match='connection_changed'):
                await request
            assert data_sdk.telemetry_plugins[-1].destroyed
            if reconnect:
                assert (await service.position()).system_id == 1
    asyncio.run(scenario())


def test_concurrent_telemetry_requests_are_independent(data_sdk):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            position, battery = await asyncio.gather(service.position(), service.battery())
            assert position.data.latitude_deg == 40.0
            assert battery.data.voltage_v == 12.5
            assert len(data_sdk.telemetry_plugins) == 2
            assert all(p.destroyed for p in data_sdk.telemetry_plugins)
    asyncio.run(scenario())


def test_information_success(data_sdk):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            result = await service.information()
            assert result.data.identification.hardware_uid == 'hardware-1'
            assert result.data.identification.legacy_uid == 1234567890123456789
            assert result.data.version.flight_sw_major == 4
            assert result.data.version.flight_sw_patch == 0
            assert result.data.version.flight_sw_version_type == 'RELEASE'
            assert result.data.errors == {}
            assert data_sdk.info_plugins[-1].destroyed
    asyncio.run(scenario())


@pytest.mark.parametrize('failed', ['identification', 'version', 'both'])
def test_partial_information_and_total_failure(data_sdk, failed):
    async def scenario():
        fields = ['identification', 'version'] if failed == 'both' else [failed]
        for field in fields:
            data_sdk.errors[field] = RuntimeError('unsupported')
        async with VehicleData(data_sdk.connection) as service:
            if failed == 'both':
                with pytest.raises(RetrievalError, match='information_unavailable'):
                    await service.information()
            else:
                result = await service.information()
                assert getattr(result.data, failed) is None
                assert 'unsupported' in result.data.errors[failed]
                available = 'version' if failed == 'identification' else 'identification'
                assert getattr(result.data, available) is not None
        assert data_sdk.info_plugins[-1].destroyed
    asyncio.run(scenario())


def test_information_timeout_shares_native_work_and_drains_on_shutdown(data_sdk, monkeypatch):
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .02)

    async def scenario():
        gate = data_sdk.gates['version'] = asyncio.Event()
        service = await VehicleData(data_sdk.connection).__aenter__()
        try:
            first = await service.information()
            assert first.data.identification is not None
            assert first.data.version is None
            assert 'timeout' in first.data.errors['version']
            second = await service.information()
            assert second.data.identification is not None
            assert data_sdk.reads['identification'] == data_sdk.reads['version'] == 1
            assert not data_sdk.info_plugins[-1].destroyed
            closing = asyncio.create_task(service.__aexit__(None, None, None))
            await asyncio.sleep(.005)
            assert not closing.done()
            gate.set()
            await closing
            assert data_sdk.info_plugins[-1].destroyed
        finally:
            gate.set()
            await service.__aexit__(None, None, None)
    asyncio.run(scenario())


def test_information_all_timeout_then_late_completion(data_sdk, monkeypatch):
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .02)

    async def scenario():
        gate = asyncio.Event()
        data_sdk.gates.update(identification=gate, version=gate)
        async with VehicleData(data_sdk.connection) as service:
            try:
                with pytest.raises(RetrievalError, match='information_unavailable.*timeout'):
                    await service.information()
                assert not data_sdk.info_plugins[-1].destroyed
            finally:
                gate.set()
        assert data_sdk.info_plugins[-1].destroyed
    asyncio.run(scenario())


def test_information_cancel_and_reconnect_do_not_reuse_old_result(data_sdk):
    async def scenario():
        gate = asyncio.Event()
        data_sdk.gates.update(identification=gate, version=gate)
        async with VehicleData(data_sdk.connection) as service:
            try:
                cancelled = asyncio.create_task(service.information())
                await wait_until(lambda: data_sdk.reads['identification'] == 1)
                cancelled.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await cancelled
                request = asyncio.create_task(service.information())
                await asyncio.sleep(.005)
                assert len(data_sdk.info_plugins) == 1
                data_sdk.connection.set_state('disconnected', 'lost')
                data_sdk.connection.set_state('connected', 'restored')
                gate.set()
                with pytest.raises(RetrievalError, match='connection_changed'):
                    await request
                result = await service.information()
                assert result.system_id == 1
                assert len(data_sdk.info_plugins) == 2
            finally:
                gate.set()
        assert all(p.destroyed for p in data_sdk.info_plugins)
    asyncio.run(scenario())
