"""MAMBA-26/27: typed reads and controlled errors through the MCP protocol."""

import asyncio
from contextlib import asynccontextmanager
import json

from fastmcp import Client

from mamba import server, vehicle_data


def test_read_tools_through_mcp(data_sdk, monkeypatch):
    @asynccontextmanager
    async def fake_connection(config_path):
        yield data_sdk.connection

    monkeypatch.setattr(server, 'vehicle_connection', fake_connection)
    monkeypatch.setattr(vehicle_data, 'REQUEST_TIMEOUT', .02)

    async def scenario():
        async with Client(server.create_server()) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            assert len(tools) == 8
            expectations = {
                'get_vehicle_information': ('identification', {'hardware_uid': 'hardware-1',
                                                              'legacy_uid': 1234567890123456789}),
                'get_vehicle_position': ('latitude_deg', 40.0),
                'get_vehicle_velocity': ('down_m_s', 3.0),
                'get_vehicle_battery': ('remaining_percent', 75.0),
                'get_vehicle_gps': ('fix_type', 'NO_FIX'),
                'get_vehicle_health': ('is_armable', False),
            }
            for name, (field, expected) in expectations.items():
                assert tools[name].annotations.readOnlyHint
                assert tools[name].inputSchema.get('properties', {}) == {}
                schema = tools[name].outputSchema
                assert {'system_id', 'received_at', 'data'} <= set(schema['properties'])
                result = await client.call_tool(name, {})
                value = json.loads(result.content[0].text)
                assert value['system_id'] == 1
                assert value['data'][field] == expected
                assert 'received_at' in value

            # A false health flag is valid data. A silent stream is a tool error.
            data_sdk.gates['position'] = asyncio.Event()
            failure = await client.call_tool('get_vehicle_position', {}, raise_on_error=False)
            assert failure.is_error
            assert 'timeout:' in failure.content[0].text
            assert data_sdk.telemetry_plugins[-1].destroyed
            data_sdk.errors['identification'] = RuntimeError('unsupported ID')
            partial = await client.call_tool('get_vehicle_information', {})
            partial_data = json.loads(partial.content[0].text)['data']
            assert partial_data['identification'] is None
            assert partial_data['version']['flight_sw_major'] == 4
            assert 'unsupported ID' in partial_data['errors']['identification']
            data_sdk.connection.set_state('disconnected', 'test disconnect')
            disconnected = await client.call_tool('get_vehicle_battery', {}, raise_on_error=False)
            assert disconnected.is_error
            assert 'not_connected:' in disconnected.content[0].text
            ping = await client.call_tool('ping', {})
            assert ping.content[0].text == 'pong'
    asyncio.run(scenario())
