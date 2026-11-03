"""MAMBA-27 / F3: selective concurrent telemetry with session-safe partial results."""

import asyncio

import pytest
from pydantic import ValidationError

from mamba import vehicle_data
from mamba.vehicle_data import RetrievalError, VehicleData


async def wait_until(predicate):
    async with asyncio.timeout(1):
        while not predicate():
            await asyncio.sleep(.001)


def test_one_requested_category_only(data_sdk):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            result = await service.telemetry(['position'])
            payload = result.model_dump(mode='json')
            assert payload['system_id'] == 1
            assert set(payload['readings']) == {'position'}
            assert payload['errors'] == {}
            assert set(payload['readings']['position']) == {'received_at', 'data'}
            assert payload['readings']['position']['data']['relative_altitude_m'] == 0
            assert dict(data_sdk.reads) == {'position': 1}
            assert all(p.destroyed for p in data_sdk.telemetry_plugins)
    asyncio.run(scenario())


def test_all_categories_preserve_nulls_zero_false_and_enums(data_sdk):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            result = await service.telemetry(['position', 'velocity', 'battery', 'gps', 'health'])
            payload = result.model_dump(mode='json')
            readings = payload['readings']
            assert set(readings) == {'position', 'velocity', 'battery', 'gps', 'health'}
            assert readings['velocity']['data']['down_m_s'] == 3
            assert readings['battery']['data']['id'] == 0
            assert readings['battery']['data']['temperature_degc'] is None
            assert readings['battery']['data']['time_remaining_s'] is None
            assert readings['battery']['data']['remaining_percent'] == 75
            assert readings['battery']['data']['battery_function'] == 'PROPULSION'
            assert readings['gps']['data'] == {'num_satellites': 0, 'fix_type': 'NO_FIX'}
            assert readings['health']['data']['is_armable'] is False
            assert result.errors == {}
            assert len(data_sdk.telemetry_plugins) == 5
            assert not data_sdk.info_plugins
    asyncio.run(scenario())


@pytest.mark.parametrize('fields', [
    [], ['position', 'position'], ['unknown'], ['POSITION'],
    ['position', 'velocity', 'battery', 'gps', 'health', 'position'],
    [1], None, 'position',
])
def test_invalid_selection_does_not_access_sdk(data_sdk, fields):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            with pytest.raises(ValidationError):
                await service.telemetry(fields)
        assert not data_sdk.telemetry_plugins and not data_sdk.reads
    asyncio.run(scenario())


def test_partial_results_and_total_failure(data_sdk):
    async def scenario():
        data_sdk.errors['gps_info'] = RuntimeError('GPS unavailable')
        async with VehicleData(data_sdk.connection) as service:
            result = await service.telemetry(['position', 'gps'])
            assert set(result.model_dump()['readings']) == {'position'}
            assert set(result.errors) == {'gps'}
            assert 'GPS unavailable' in result.errors['gps']
            data_sdk.errors['position'] = RuntimeError('position unavailable')
            with pytest.raises(RetrievalError, match='telemetry_unavailable:.*position:.*gps:'):
                await service.telemetry(['position', 'gps'])
        assert all(p.destroyed for p in data_sdk.telemetry_plugins)
    asyncio.run(scenario())


def test_shared_deadline_and_concurrent_start(data_sdk, monkeypatch):
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .06)

    async def scenario():
        data_sdk.gates['battery'] = asyncio.Event()
        data_sdk.gates['health'] = asyncio.Event()
        async with VehicleData(data_sdk.connection) as service:
            start = asyncio.get_running_loop().time()
            request = asyncio.create_task(service.telemetry(['position', 'battery', 'health']))
            await wait_until(lambda: all(data_sdk.reads[t] == 1
                                        for t in ['position', 'battery', 'health']))
            assert not request.done()
            result = await request
            elapsed = asyncio.get_running_loop().time() - start
            assert .04 <= elapsed < .15, elapsed
            assert set(result.model_dump()['readings']) == {'position'}
            assert set(result.errors) == {'battery', 'health'}
            assert all('timeout' in error for error in result.errors.values())
            assert all(p.destroyed and not p.active for p in data_sdk.telemetry_plugins)
    asyncio.run(scenario())


def test_total_timeout_returns_tool_failure(data_sdk, monkeypatch):
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .02)

    async def scenario():
        data_sdk.gates['position'] = asyncio.Event()
        async with VehicleData(data_sdk.connection) as service:
            with pytest.raises(RetrievalError, match='telemetry_unavailable:.*timeout'):
                await service.telemetry(['position'])
        assert data_sdk.telemetry_plugins[-1].destroyed
    asyncio.run(scenario())


@pytest.mark.parametrize('reconnect', [False, True])
def test_connection_change_discards_completed_categories(data_sdk, reconnect):
    async def scenario():
        gate = data_sdk.gates['battery'] = asyncio.Event()
        async with VehicleData(data_sdk.connection) as service:
            request = asyncio.create_task(service.telemetry(['position', 'battery']))
            await wait_until(lambda: data_sdk.reads['battery'] == 1)
            assert data_sdk.telemetry_plugins[0].destroyed  # Position already succeeded.
            data_sdk.connection.set_state('disconnected', 'lost')
            if reconnect:
                data_sdk.connection.set_state('connected', 'restored')
            gate.set()
            with pytest.raises(RetrievalError, match='connection_changed'):
                await request
            assert all(p.destroyed for p in data_sdk.telemetry_plugins)
            if reconnect:
                result = await service.telemetry(['position'])
                assert result.system_id == 1
    asyncio.run(scenario())


def test_invalid_target_in_one_category_fails_entire_batch(data_sdk, monkeypatch):
    async def scenario():
        async with VehicleData(data_sdk.connection) as service:
            async def bad_position():
                raise RetrievalError('invalid_target: transient target mismatch')
            monkeypatch.setattr(service, 'position', bad_position)
            with pytest.raises(RetrievalError, match='invalid_target:'):
                await service.telemetry(['position', 'battery'])
            assert data_sdk.telemetry_plugins[-1].destroyed
    asyncio.run(scenario())


def test_caller_cancellation_closes_every_subscription(data_sdk):
    async def scenario():
        data_sdk.gates.update(position=asyncio.Event(), battery=asyncio.Event())
        async with VehicleData(data_sdk.connection) as service:
            request = asyncio.create_task(service.telemetry(['position', 'battery']))
            await wait_until(lambda: data_sdk.reads['position'] == data_sdk.reads['battery'] == 1)
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
            assert all(p.destroyed and not p.active for p in data_sdk.telemetry_plugins)
    asyncio.run(scenario())


def test_shutdown_drains_parent_and_child_requests(data_sdk):
    async def scenario():
        data_sdk.gates.update(position=asyncio.Event(), battery=asyncio.Event())
        service = await VehicleData(data_sdk.connection).__aenter__()
        request = asyncio.create_task(service.telemetry(['position', 'battery']))
        await wait_until(lambda: data_sdk.reads['position'] == data_sdk.reads['battery'] == 1)
        await asyncio.wait_for(service.__aexit__(None, None, None), timeout=1)
        assert request.cancelled()
        assert all(p.destroyed and not p.active for p in data_sdk.telemetry_plugins)
        assert not service._calls
    asyncio.run(scenario())
