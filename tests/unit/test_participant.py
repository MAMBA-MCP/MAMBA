"""MAMBA-28/29: reject invalid reports before the permissive native encoder."""

import json
import xml.etree.ElementTree as ET

import pytest
from pydantic import ValidationError

from mamba.participant import ParticipantPosition, participant_xml, pinned_dialect
from mamba import participant
from mamba.vehicle_data import TelemetryReadings, TelemetryResult


def sample(**changes):
    return ParticipantPosition(time_usec=1793734000123456, lat=400000000,
        lon=-740000000, callsign="MAMBA-SIM", origin_sysid=1, **changes)


@pytest.mark.parametrize("field,value", [
    ("time_usec", 0), ("time_usec", 2**64), ("time_usec", True),
    ("lat", 900000001), ("lon", -1800000001), ("lat", True),
    ("origin_sysid", 0), ("origin_sysid", 256), ("origin_sysid", "1"),
    ("callsign", ""), ("callsign", "x" * 50), ("callsign", "a\0b"),
    ("callsign", "café"), ("external_track_number", "x" * 20),
    ("alt", float("inf")), ("vx", float("nan")), ("vy", 1e39),
    ("course", 360.0), ("course", -1.0), ("ppli_type", 5),
    ("stanag_identity", 7), ("external_track_type", 4), ("unexpected", 1),
])
def test_invalid_wire_input_rejected(field, value):
    values = sample().model_dump() | {field: value}
    with pytest.raises(ValidationError):
        ParticipantPosition.model_validate(values)


def test_unknowns_remain_null_until_native_encoding():
    fields = json.loads(sample().to_message(component_id=191).fields_json)
    assert all(fields[key] is None for key in ["alt", "vx", "vy", "vz", "course"])
    assert fields["stanag_identity"] == 1  # Unknown, never assumed friendly.
    assert fields["external_track_type"] == fields["ppli_type"] == 0


@pytest.mark.parametrize("component", [0, 256, True, "191"])
def test_invalid_source_component_rejected(component):
    with pytest.raises(ValueError):
        sample().to_message(component_id=component)


def telemetry():
    return TelemetryResult(system_id=17, errors={}, readings=TelemetryReadings(
        position={"received_at": "2026-11-03T19:00:00+00:00", "data": {
            "latitude_deg": -35.363262, "longitude_deg": 149.1652373,
            "absolute_altitude_m": 584.09, "relative_altitude_m": 10.0}},
        velocity={"received_at": "2026-11-03T19:00:00.100000+00:00", "data": {
            "north_m_s": 1.25, "east_m_s": -2.5, "down_m_s": .75}}))


def test_telemetry_mapping_preserves_units_and_origin():
    mapped = ParticipantPosition.from_telemetry(telemetry(), time_usec=1793734000123456,
                                               callsign="MAMBA-SIM")
    assert mapped.lat == -353632620 and mapped.lon == 1491652373
    assert mapped.alt == 584.09  # AMSL, not relative altitude.
    assert (mapped.vx, mapped.vy, mapped.vz) == (1.25, -2.5, .75)
    assert mapped.origin_sysid == 17
    assert mapped.time_usec == 1793734000123456
    assert mapped.course is None  # No heading/course invented from stationary data.
    message = mapped.to_message(component_id=191)
    assert message.message_name == "PARTICIPANT_POSITION"
    assert (message.system_id, message.component_id) == (17, 191)
    assert (message.target_system_id, message.target_component_id) == (0, 0)


@pytest.mark.parametrize("kind", ["position", "velocity", "coordinates", "error"])
def test_unavailable_telemetry_cannot_form_report(kind):
    data = telemetry()
    if kind in ["position", "velocity"]:
        setattr(data.readings, kind, None)
    elif kind == "coordinates":
        data.readings.position.data.latitude_deg = None
    else:
        data.errors["position"] = "timeout"
    with pytest.raises(ValueError):
        ParticipantPosition.from_telemetry(data, time_usec=1, callsign="MAMBA-SIM")


def test_scoped_xml_preserves_original_message_and_only_its_enums():
    original = ET.fromstring(pinned_dialect())
    scoped = ET.fromstring(participant_xml())
    messages = scoped.findall("./messages/message")
    assert len(messages) == 1 and messages[0].attrib == {
        "id": "53003", "name": "PARTICIPANT_POSITION"}
    source = original.find("./messages/message[@name='PARTICIPANT_POSITION']")
    assert ET.tostring(messages[0]) == ET.tostring(source)
    expected = {field.attrib["enum"] for field in source.findall("field") if "enum" in field.attrib}
    assert {enum.attrib["name"] for enum in scoped.findall("./enums/enum")} == expected
    assert scoped.find("include") is None


def test_schema_drift_rejected(tmp_path, monkeypatch):
    path = tmp_path / "military.xml"
    path.write_text(pinned_dialect() + "\n")
    monkeypatch.setattr(participant, "DIALECT_PATH", path)
    with pytest.raises(ValueError, match="checksum"):
        participant_xml()


def test_bypassing_model_validation_cannot_bypass_native_boundary():
    invalid = sample().model_copy(update={"origin_sysid": 256})
    with pytest.raises(ValidationError):
        invalid.to_message(component_id=191)
