"""F2/A02 (MAMBA-2): identity matching, connection failures, and recovery."""

import asyncio
from contextlib import suppress

import pytest

from mamba import connection as connection_module


@pytest.mark.parametrize("body", [
    '', '[other]\nsystem_id = 1',
    '[vehicle]\nsystem_id = 1',
    '[vehicle]\nconnection_url = "udpin://127.0.0.1:14540"\nsystem_id = true',
    '[vehicle]\nconnection_url = "udpin://127.0.0.1:14540"\nsystem_id = 0',
    '[vehicle]\nconnection_url = "udpin://127.0.0.1:14540"\nsystem_id = 256',
    '[vehicle]\nconnection_url = "udp://:14540"\nsystem_id = 1',
    '[vehicle]\nconnection_url = "udpin://localhost:65536"\nsystem_id = 1',
    '[vehicle]\nconnection_url = "udpin://localhost:14540/path"\nsystem_id = 1',
    '[vehicle]\nconnection_url = "serial:///dev/ttyUSB0:0"\nsystem_id = 1',
    '[vehicle]\nconnection_url = "serial:///dev/ttyUSB0:57600"\nsystem_id = 1\nextra = 2',
    '[vehicle',
])
def test_invalid_config(tmp_path, body):
    path = tmp_path / 'vehicle.toml'
    path.write_text(body)
    with pytest.raises(ValueError):
        connection_module.VehicleConfig.load(path)


@pytest.mark.parametrize('url', [
    'udpin://127.0.0.1:14540', 'udpout://localhost:14550',
    'tcpout://127.0.0.1:5760', 'tcpin://0.0.0.0:5760',
    'serial:///dev/ttyUSB0:57600', 'serial://COM3:115200',
])
def test_valid_config(tmp_path, url):
    path = tmp_path / 'vehicle.toml'
    path.write_text(f'[vehicle]\nconnection_url = "{url}"\nsystem_id = 1\n')
    assert connection_module.VehicleConfig.load(path) == connection_module.VehicleConfig(url, 1)


class FakeSystem:
    def __init__(self, system_id, connected=True, autopilot=True):
        self.system_id = system_id
        self.connected = connected
        self.autopilot = autopilot

    async def get_system_id(self):
        return self.system_id

    async def is_connected(self):
        return self.connected

    async def has_autopilot(self):
        return self.autopilot


class FakeSDK:
    def __init__(self):
        self.systems = []
        self.add_calls = 0
        self.destroyed = False
        self.add_error = None
        self.scan_error = None

    async def add_any_connection(self, url):
        self.add_calls += 1
        if self.add_error:
            raise self.add_error

    async def get_systems(self):
        if self.scan_error:
            raise self.scan_error
        return self.systems

    def destroy(self):
        self.destroyed = True


async def wait_state(connection, state):
    async with asyncio.timeout(1):
        while connection.status.state != state:
            await asyncio.sleep(.001)


async def stop(task):
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@pytest.fixture
def setup_connection(monkeypatch):
    sdk = FakeSDK()
    monkeypatch.setattr(connection_module, 'Mavsdk', lambda _: sdk)
    monkeypatch.setattr(connection_module, 'DISCOVERY_TIMEOUT', .025)
    monkeypatch.setattr(connection_module, 'RETRY_INTERVAL', .01)
    monkeypatch.setattr(connection_module, 'POLL_INTERVAL', .001)
    return connection_module.VehicleConnection(connection_module.VehicleConfig('udpin://127.0.0.1:14540', 1)), sdk


def test_discovery_identity_disconnect_recovery(setup_connection):
    async def scenario():
        connection, sdk = setup_connection
        target = FakeSystem(1)
        sdk.systems = [FakeSystem(2), FakeSystem(3, autopilot=False), target]
        task = asyncio.create_task(connection.run())
        try:
            await wait_state(connection, 'connected')
            assert connection.system is target
            assert connection.status.discovered_system_ids == (1, 2)
            first_change = connection.status.last_changed_at
            await asyncio.sleep(.005)
            assert connection.status.last_changed_at == first_change
            target.connected = False
            await wait_state(connection, 'disconnected')
            assert connection.system is None
            assert connection.status.last_changed_at != first_change
            target.connected = True
            await wait_state(connection, 'connected')
            assert sdk.add_calls == 1  # Transport persists across discovery and link loss.
        finally:
            await stop(task)
        assert sdk.destroyed
    asyncio.run(scenario())


def test_nonmatching_id_timeout_then_recovery(setup_connection):
    async def scenario():
        connection, sdk = setup_connection
        sdk.systems = [FakeSystem(2), FakeSystem(1, autopilot=False)]
        task = asyncio.create_task(connection.run())
        try:
            await wait_state(connection, 'error')
            assert 'timed out' in connection.status.reason
            assert connection.system is None
            assert connection.status.discovered_system_ids == (2,)
            sdk.systems.append(FakeSystem(1))
            await wait_state(connection, 'connected')
            assert sdk.add_calls == 1
        finally:
            await stop(task)
    asyncio.run(scenario())


def test_transport_error_retries_without_server_exit(setup_connection):
    async def scenario():
        connection, sdk = setup_connection
        sdk.add_error = RuntimeError('bad connection URI or occupied port')
        task = asyncio.create_task(connection.run())
        try:
            await wait_state(connection, 'error')
            assert 'bad connection URI' in connection.status.reason
            assert not task.done()
            sdk.add_error = None
            sdk.systems = [FakeSystem(1)]
            await wait_state(connection, 'connected')
            assert sdk.add_calls >= 2
            sdk.scan_error = RuntimeError('SDK failure')
            await wait_state(connection, 'error')
            assert connection.system is None
            sdk.scan_error = None
            await wait_state(connection, 'connected')
        finally:
            await stop(task)
        assert sdk.destroyed
    asyncio.run(scenario())


def test_duplicate_matching_ids_rejected(setup_connection):
    async def scenario():
        connection, sdk = setup_connection
        sdk.systems = [FakeSystem(1), FakeSystem(1)]
        task = asyncio.create_task(connection.run())
        try:
            await wait_state(connection, 'error')
            assert 'Multiple autopilots' in connection.status.reason
            assert connection.system is None
        finally:
            await stop(task)
    asyncio.run(scenario())


def test_unconfigured():
    connection = connection_module.VehicleConnection()
    asyncio.run(connection.run())
    assert connection.status.state == 'unconfigured'
    assert connection.sdk is None


def test_connection_timeout_is_reported(setup_connection):
    async def scenario():
        connection, sdk = setup_connection

        release_setup = asyncio.Event()

        async def hanging_add(url):
            sdk.add_calls += 1
            await release_setup.wait()

        sdk.add_any_connection = hanging_add
        task = asyncio.create_task(connection.run())
        try:
            await wait_state(connection, 'error')
            assert connection.status.reason == 'MAVSDK connection timed out'
            assert not task.done()
            await asyncio.sleep(.08)
            assert sdk.add_calls == 1  # Timed-out native setup is still in flight.
            sdk.systems = [FakeSystem(1)]
            release_setup.set()
            await wait_state(connection, 'connected')
            assert sdk.add_calls == 1
        finally:
            release_setup.set()
            await stop(task)
        assert sdk.destroyed
    asyncio.run(scenario())
