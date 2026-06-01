from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SourceType(StrEnum):
    RBN_CW_RTTY = "RBN_CW_RTTY"
    RBN_FT8 = "RBN_FT8"
    CLASSIC_CLUSTER = "CLASSIC_CLUSTER"
    DXSUMMIT = "DXSUMMIT"
    PSKREPORTER = "PSKREPORTER"
    WSPRNET = "WSPRNET"
    LOCAL_SKIMMER = "LOCAL_SKIMMER"


class EndpointState(StrEnum):
    DISABLED = "disabled"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    STANDBY = "standby"


class FeedStrategy(StrEnum):
    ACTIVE_ACTIVE = "active_active"
    ACTIVE_PASSIVE = "active_passive"
    PRIORITY_FAILOVER = "priority_failover"


@dataclass(slots=True)
class SourceEvidence:
    source_type: SourceType
    endpoint_name: str
    source_instance: str
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Spot:
    source: str
    source_type: SourceType
    spotter_callsign: str
    spotted_callsign: str
    frequency_khz: float
    band: str | None
    mode: str | None
    comment: str | None = None
    snr: int | None = None
    speed_wpm: int | None = None
    cq_zone: int | None = None
    itu_zone: int | None = None
    spotter_country: str | None = None
    spotted_country: str | None = None
    spotter_grid: str | None = None
    spotted_grid: str | None = None
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    raw_line: str = ""
    is_rbn: bool = False
    is_skimmer: bool = False
    is_human_spot: bool = False
    confidence_score: float = 0.5
    endpoint_name: str = "unknown"
    source_instance: str = "unknown"
    duplicate_sources: list[SourceEvidence] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def supporting_sources(self) -> list[SourceEvidence]:
        return self.duplicate_sources

    def add_evidence(self, evidence: SourceEvidence) -> None:
        key = (evidence.source_type, evidence.endpoint_name, evidence.source_instance)
        existing = {
            (e.source_type, e.endpoint_name, e.source_instance) for e in self.duplicate_sources
        }
        if key not in existing:
            self.duplicate_sources.append(evidence)
            self.confidence_score = min(1.0, self.confidence_score + 0.1)

    def to_record(self) -> dict[str, Any]:
        data = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "duplicate_sources"
        }
        data["source_type"] = str(self.source_type)
        data["timestamp_utc"] = self.timestamp_utc.isoformat()
        data["duplicate_sources"] = [
            asdict(e)
            | {"source_type": str(e.source_type), "timestamp_utc": e.timestamp_utc.isoformat()}
            for e in self.duplicate_sources
        ]
        return data


@dataclass(slots=True)
class EndpointMetrics:
    state: EndpointState = EndpointState.DISABLED
    reconnect_count: int = 0
    last_message_utc: datetime | None = None
    spots_received: int = 0
    parse_errors: int = 0
    messages_window: list[datetime] = field(default_factory=list)
    active: bool = False

    def mark_message(self, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        self.last_message_utc = now
        self.spots_received += 1
        self.messages_window.append(now)
        cutoff = now.timestamp() - 60
        self.messages_window = [t for t in self.messages_window if t.timestamp() >= cutoff]

    @property
    def messages_per_minute(self) -> float:
        return float(len(self.messages_window))


@dataclass(slots=True)
class EndpointStatus:
    category: SourceType
    name: str
    host: str
    port: int
    state: EndpointState
    spots_per_minute: float
    last_message_utc: datetime | None
    reconnects: int
    spots_received: int
    parse_errors: int
    enabled: bool
