"""Measure MCP descriptors and fixed example payloads from the checkout in cwd."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd() / 'src'))
from mamba.server import create_server
from mamba import vehicle_data as data


def size(value):
    return len(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))


async def main():
    tools = await create_server().get_tools()
    descriptors = [tools[name].to_mcp_tool().model_dump(mode='json', by_alias=True, exclude_none=True)
                   for name in sorted(tools)]
    telemetry_names = {'get_vehicle_position', 'get_vehicle_velocity', 'get_vehicle_battery',
                       'get_vehicle_gps', 'get_vehicle_health', 'get_vehicle_telemetry'}
    telemetry_descriptors = [tool for tool in descriptors if tool['name'] in telemetry_names]
    values = {
        'position': data.PositionData(latitude_deg=40, longitude_deg=-74, absolute_altitude_m=125.5,
                                      relative_altitude_m=0),
        'battery': data.BatteryData(id=0, voltage_v=12.5, current_battery_a=0,
                                    remaining_percent=75, battery_function='PROPULSION'),
        'health': data.HealthData(is_gyrometer_calibration_ok=False, is_accelerometer_calibration_ok=True,
                                  is_magnetometer_calibration_ok=False, is_local_position_ok=False,
                                  is_global_position_ok=False, is_home_position_ok=True, is_armable=False),
    }
    timestamp = '2026-11-03T12:00:00+00:00'

    def response_size(fields):
        if 'get_vehicle_telemetry' in tools:
            readings = data.TelemetryReadings(**{
                field: data.TelemetrySample[type(values[field])](received_at=timestamp, data=values[field])
                for field in fields
            })
            return size(data.TelemetryResult(system_id=1, readings=readings, errors={}).model_dump(mode='json'))
        return sum(size(data.Reading[type(values[field])](
            system_id=1, received_at=timestamp, data=values[field]).model_dump(mode='json')) for field in fields)

    result = {
        'tool_count': len(tools),
        'catalog_bytes': size(descriptors),
        'telemetry_descriptors_bytes': size(telemetry_descriptors),
        'position_response_bytes': response_size(['position']),
        'position_battery_health_response_bytes': response_size(['position', 'battery', 'health']),
    }
    Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == "__main__":
    asyncio.run(main())
