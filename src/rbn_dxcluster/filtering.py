from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import Spot


@dataclass(slots=True)
class SpotFilter:
    bands: set[str] = field(default_factory=set)
    modes: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    include_skimmer: bool = True
    include_human: bool = True
    min_snr: int | None = None
    callsign_include_regex: str | None = None
    callsign_exclude_regex: str | None = None
    spotter_include_regex: str | None = None
    spotter_exclude_regex: str | None = None
    nodupes: bool = True

    def allows(self, spot: Spot) -> bool:
        if self.bands and (spot.band or "").lower() not in {b.lower() for b in self.bands}:
            return False
        if self.modes and (spot.mode or "UNKNOWN").upper() not in {m.upper() for m in self.modes}:
            return False
        if self.sources and str(spot.source_type).upper() not in {s.upper() for s in self.sources}:
            return False
        if spot.is_skimmer and not self.include_skimmer:
            return False
        if spot.is_human_spot and not self.include_human:
            return False
        if self.min_snr is not None and (spot.snr is None or spot.snr < self.min_snr):
            return False
        if self.callsign_include_regex and not re.search(
            self.callsign_include_regex, spot.spotted_callsign, re.I
        ):
            return False
        if self.callsign_exclude_regex and re.search(
            self.callsign_exclude_regex, spot.spotted_callsign, re.I
        ):
            return False
        if self.spotter_include_regex and not re.search(
            self.spotter_include_regex, spot.spotter_callsign, re.I
        ):
            return False
        if self.spotter_exclude_regex and re.search(
            self.spotter_exclude_regex, spot.spotter_callsign, re.I
        ):
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "bands": sorted(self.bands),
            "modes": sorted(self.modes),
            "sources": sorted(self.sources),
            "include_skimmer": self.include_skimmer,
            "include_human": self.include_human,
            "min_snr": self.min_snr,
            "callsign_include_regex": self.callsign_include_regex,
            "callsign_exclude_regex": self.callsign_exclude_regex,
            "spotter_include_regex": self.spotter_include_regex,
            "spotter_exclude_regex": self.spotter_exclude_regex,
            "nodupes": self.nodupes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpotFilter:
        return cls(
            bands={str(v).lower() for v in data.get("bands", [])},
            modes={str(v).upper() for v in data.get("modes", [])},
            sources={str(v).upper() for v in data.get("sources", [])},
            include_skimmer=bool(data.get("include_skimmer", True)),
            include_human=bool(data.get("include_human", True)),
            min_snr=data.get("min_snr"),
            callsign_include_regex=data.get("callsign_include_regex"),
            callsign_exclude_regex=data.get("callsign_exclude_regex"),
            spotter_include_regex=data.get("spotter_include_regex"),
            spotter_exclude_regex=data.get("spotter_exclude_regex"),
            nodupes=bool(data.get("nodupes", True)),
        )
