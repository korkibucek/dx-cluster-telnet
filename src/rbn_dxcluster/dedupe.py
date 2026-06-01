from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime, timedelta

from .models import SourceEvidence, Spot


class SpotDeduplicator:
    def __init__(self, window_seconds: int = 60, frequency_tolerance_khz: float = 0.5) -> None:
        self.window = timedelta(seconds=window_seconds)
        self.frequency_tolerance_khz = frequency_tolerance_khz
        self._spots: OrderedDict[str, Spot] = OrderedDict()
        self.duplicates = 0
        self.accepted = 0

    def _signature(self, spot: Spot) -> str:
        bucket = round(spot.frequency_khz / self.frequency_tolerance_khz)
        return "|".join(
            [
                spot.spotted_callsign.upper(),
                str(bucket),
                spot.band or "",
                spot.mode or "",
            ]
        )

    def process(self, spot: Spot) -> tuple[bool, Spot]:
        now = spot.timestamp_utc
        self._expire(now)
        signature = self._signature(spot)
        existing = self._spots.get(signature)
        if (
            existing
            and abs((now - existing.timestamp_utc).total_seconds()) <= self.window.total_seconds()
        ):
            existing.add_evidence(
                SourceEvidence(spot.source_type, spot.endpoint_name, spot.source_instance, now)
            )
            self.duplicates += 1
            return False, existing
        spot.add_evidence(
            SourceEvidence(spot.source_type, spot.endpoint_name, spot.source_instance, now)
        )
        self._spots[signature] = spot
        self.accepted += 1
        return True, spot

    def _expire(self, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        expired = [
            key for key, spot in self._spots.items() if now - spot.timestamp_utc > self.window
        ]
        for key in expired:
            self._spots.pop(key, None)
