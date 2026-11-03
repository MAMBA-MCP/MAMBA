"""Pinned own-platform position mapping; not registered as an MCP tool.

Transport integration is exercised only by the opt-in loopback simulation.
This module does not establish source freshness, identity authentication or
permission to publish, and does not expose generic custom-message dispatch.
"""

from copy import deepcopy
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from mavsdk.asyncio.plugins.mavlink_direct import MavlinkMessage
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .vehicle_data import TelemetryResult

ROOT = Path(__file__).resolve().parents[2]
DIALECT_PATH = ROOT / "third_party/mavlink-m/military.xml"
DIALECT_SHA256 = "02a88f79b9b4e58b271d9b0012a06087ac4ec975c75a8b1d7ba704c43bb55a8f"
MESSAGE_NAME = "PARTICIPANT_POSITION"
MESSAGE_ID = 53003
FLOAT32_MAX = 3.4028234663852886e38


def pinned_dialect() -> str:
    """Reject accidental schema drift before loading or generating bindings."""
    content = DIALECT_PATH.read_bytes()
    if hashlib.sha256(content).hexdigest() != DIALECT_SHA256:
        raise ValueError("MAVLink-M dialect checksum does not match the pinned revision")
    return content.decode("utf-8")


def participant_xml() -> str:
    """Extract the original message and its enums without unresolved includes."""
    source = ET.fromstring(pinned_dialect())
    message = source.find(f"./messages/message[@name='{MESSAGE_NAME}']")
    if message is None or int(message.attrib["id"]) != MESSAGE_ID:
        raise ValueError("Pinned participant message is missing or has a different ID")
    root = ET.Element("mavlink")
    enums = ET.SubElement(root, "enums")
    names = {field.attrib["enum"] for field in message.findall("field") if "enum" in field.attrib}
    for enum in source.findall("./enums/enum"):
        if enum.attrib["name"] in names:
            enums.append(deepcopy(enum))
    ET.SubElement(root, "messages").append(deepcopy(message))
    return ET.tostring(root, encoding="unicode")


class ParticipantPosition(BaseModel):
    """Exact wire fields with bounds checked before native JSON conversion."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, frozen=True)

    time_usec: int = Field(gt=0, le=2**64 - 1)
    lat: int = Field(ge=-900_000_000, le=900_000_000)
    lon: int = Field(ge=-1_800_000_000, le=1_800_000_000)
    alt: float | None = Field(default=None, ge=-FLOAT32_MAX, le=FLOAT32_MAX)
    vx: float | None = Field(default=None, ge=-FLOAT32_MAX, le=FLOAT32_MAX)
    vy: float | None = Field(default=None, ge=-FLOAT32_MAX, le=FLOAT32_MAX)
    vz: float | None = Field(default=None, ge=-FLOAT32_MAX, le=FLOAT32_MAX)
    course: float | None = Field(default=None, ge=0, lt=360)
    external_track_number: str = Field(default="", max_length=19)
    callsign: str = Field(min_length=1, max_length=49)
    origin_sysid: int = Field(ge=1, le=255)
    # No external namespace or identity/type classification is inferred.
    external_track_type: int = Field(default=0, ge=0, le=3)
    stanag_identity: int = Field(default=1, ge=0, le=6)
    ppli_type: int = Field(default=0, ge=0, le=4)

    @field_validator("external_track_number", "callsign")
    @classmethod
    def ascii_text(cls, value: str) -> str:
        if not value.isascii() or "\0" in value:
            raise ValueError("MAVLink char arrays require ASCII text without embedded NUL")
        return value

    def to_message(self, *, component_id: int) -> MavlinkMessage:
        """Build an envelope; configure the SDK with the same source IDs.

        MAVSDK 4.0.6 ignores these per-message source overrides on the wire.
        The simulation validates the actual configured sender independently.
        """
        if type(component_id) is not int or not 1 <= component_id <= 255:
            raise ValueError("component_id must be an integer from 1 to 255")
        # model_copy/model_construct can bypass Pydantic validation. Validate
        # again at the boundary before handing anything to the native encoder.
        validated = type(self).model_validate(self.model_dump())
        return MavlinkMessage(
            message_name=MESSAGE_NAME, system_id=validated.origin_sysid,
            component_id=component_id, target_system_id=0, target_component_id=0,
            fields_json=validated.model_dump_json(),
        )

    @classmethod
    def from_telemetry(cls, telemetry: TelemetryResult, *, time_usec: int,
                       callsign: str) -> "ParticipantPosition":
        """Map SDK units; caller supplies report-assembly UTC microseconds.

        Receipt timestamps are not a vehicle sensor clock. Transport callers
        must retain them and validate their own session/freshness requirements.
        """
        readings = telemetry.readings
        if (readings.position is None or readings.velocity is None
                or "position" in telemetry.errors or "velocity" in telemetry.errors):
            raise ValueError("Position and velocity readings are required")
        position, velocity = readings.position.data, readings.velocity.data
        if position.latitude_deg is None or position.longitude_deg is None:
            raise ValueError("Latitude and longitude must be known")
        if not (-90 <= position.latitude_deg <= 90 and -180 <= position.longitude_deg <= 180):
            raise ValueError("Telemetry coordinates are out of range")
        return cls(
            time_usec=time_usec, callsign=callsign, origin_sysid=telemetry.system_id,
            lat=round(position.latitude_deg * 1e7), lon=round(position.longitude_deg * 1e7),
            alt=position.absolute_altitude_m, vx=velocity.north_m_s,
            vy=velocity.east_m_s, vz=velocity.down_m_s,
        )
