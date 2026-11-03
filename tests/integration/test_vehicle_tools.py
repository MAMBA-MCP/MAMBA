"""MAMBA-26/27: consolidated telemetry schemas, partial results, and MCP errors."""

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
            assert set(tools) == {
                'ping', 'get_vehicle_status', 'get_vehicle_information', 'get_vehicle_telemetry',
            }
            tool = tools['get_vehicle_telemetry']
            assert tool.annotations.readOnlyHint
            assert tool.inputSchema['required'] == ['fields']
            field_schema = tool.inputSchema['properties']['fields']
            assert set(field_schema['items']['enum']) == {'position', 'velocity', 'battery', 'gps', 'health'}
            assert field_schema['minItems'] == 1 and field_schema['maxItems'] == 5
            assert field_schema['uniqueItems'] is True
            assert {'system_id', 'readings', 'errors'} <= set(tool.outputSchema['properties'])

            for arguments in [{}, {'fields': []}, {'fields': ['unknown']},
                              {'fields': ['position', 'position']}]:
                failure = await client.call_tool('get_vehicle_telemetry', arguments, raise_on_error=False)
                assert failure.is_error
            assert not data_sdk.telemetry_plugins
            for old in ['position', 'velocity', 'battery', 'gps', 'health']:
                failure = await client.call_tool(f'get_vehicle_{old}', {}, raise_on_error=False)
                assert failure.is_error

            info_tool = tools['get_vehicle_information']
            assert info_tool.annotations.readOnlyHint
            assert info_tool.inputSchema.get('properties', {}) == {}
            info = await client.call_tool('get_vehicle_information', {})
            info_value = json.loads(info.content[0].text)
            assert info_value['system_id'] == 1
            assert info_value['data']['identification']['hardware_uid'] == 'hardware-1'
            assert 'received_at' in info_value

            result = await client.call_tool('get_vehicle_telemetry', {
                'fields': ['position', 'velocity', 'battery', 'gps', 'health'],
            })
            payload = json.loads(result.content[0].text)
            assert payload['system_id'] == 1
            assert payload['errors'] == {}
            for field, (key, expected) in {
                'position': ('latitude_deg', 40.0), 'velocity': ('down_m_s', 3.0),
                'battery': ('remaining_percent', 75.0), 'gps': ('fix_type', 'NO_FIX'),
                'health': ('is_armable', False),
            }.items():
                assert payload['readings'][field]['data'][key] == expected
                assert set(payload['readings'][field]) == {'received_at', 'data'}
            assert payload['readings']['battery']['data']['temperature_degc'] is None

            # Only requested successful categories are emitted; nested unknowns remain null.
            selected = await client.call_tool('get_vehicle_telemetry', {'fields': ['battery']})
            selected_payload = json.loads(selected.content[0].text)
            assert set(selected_payload['readings']) == {'battery'}
            assert selected_payload['readings']['battery']['data']['time_remaining_s'] is None

            data_sdk.gates['position'] = asyncio.Event()
            partial = await client.call_tool('get_vehicle_telemetry', {'fields': ['position', 'battery']})
            partial_payload = json.loads(partial.content[0].text)
            assert set(partial_payload['readings']) == {'battery'}
            assert set(partial_payload['errors']) == {'position'}
            assert 'timeout:' in partial_payload['errors']['position']
            failure = await client.call_tool('get_vehicle_telemetry', {'fields': ['position']},
                                             raise_on_error=False)
            assert failure.is_error and 'telemetry_unavailable:' in failure.content[0].text
            assert all(plugin.destroyed for plugin in data_sdk.telemetry_plugins)

            data_sdk.errors['identification'] = RuntimeError('unsupported ID')
            partial_info = await client.call_tool('get_vehicle_information', {})
            partial_info_data = json.loads(partial_info.content[0].text)['data']
            assert partial_info_data['identification'] is None
            assert partial_info_data['version']['flight_sw_major'] == 4
            assert 'unsupported ID' in partial_info_data['errors']['identification']
            data_sdk.connection.set_state('disconnected', 'test disconnect')
            disconnected = await client.call_tool('get_vehicle_telemetry', {'fields': ['battery']},
                                                  raise_on_error=False)
            assert disconnected.is_error
            assert 'not_connected:' in disconnected.content[0].text
            ping = await client.call_tool('ping', {})
            assert ping.content[0].text == 'pong'
    asyncio.run(scenario())
