"""F1/A01, F2/A02: real stdio MCP sessions and native MAVSDK startup."""

import asyncio
import json
from pathlib import Path
import socket
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[2] / 'src/mamba/server.py'


async def read_status(session):
    result = await session.call_tool('get_vehicle_status', {})
    assert not result.isError, result
    return json.loads(result.content[0].text)


@pytest.mark.parametrize('config_kind', ['absent', 'missing', 'invalid'])
def test_stdio_status_and_ping(tmp_path, config_kind):
    args = [str(SERVER)]
    if config_kind != 'absent':
        path = tmp_path / 'vehicle.toml'
        if config_kind == 'invalid':
            path.write_text('[vehicle]\nsystem_id = 0\n')
        args.extend(['--config', str(path)])

    async def scenario():
        async with asyncio.timeout(20):
            params = StdioServerParameters(command=sys.executable, args=args)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert {t.name for t in tools.tools} == {'ping', 'get_vehicle_status'}
                    status_tool = next(t for t in tools.tools if t.name == 'get_vehicle_status')
                    assert status_tool.annotations.readOnlyHint
                    first = await read_status(session)
                    assert first['state'] == ('unconfigured' if config_kind == 'absent' else 'error')
                    assert first['system_id'] is None
                    result = await session.call_tool('ping', {})
                    assert result.content[0].text == 'pong'
                    second = await read_status(session)
                    assert first['last_changed_at'] == second['last_changed_at']
    asyncio.run(scenario())


def test_native_mavsdk_timeout_keeps_mcp_alive(tmp_path):
    # An ephemeral loopback endpoint with no sender; no hardware is contacted.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    path = tmp_path / 'vehicle.toml'
    path.write_text(f'[vehicle]\nconnection_url = "udpin://127.0.0.1:{port}"\nsystem_id = 1\n')

    async def scenario():
        async with asyncio.timeout(30):
            params = StdioServerParameters(
                command=sys.executable, args=[str(SERVER), '--config', str(path)]
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    status = await read_status(session)
                    assert status['state'] == 'connecting', status
                    assert status['system_id'] == 1
                    while status['state'] != 'error':
                        await asyncio.sleep(.1)
                        status = await read_status(session)
                    assert 'timed out' in status['reason'], status
                    assert status['discovered_system_ids'] == []
                    assert status['last_checked_at'] is not None
                    result = await session.call_tool('ping', {})
                    assert result.content[0].text == 'pong'
    asyncio.run(scenario())
