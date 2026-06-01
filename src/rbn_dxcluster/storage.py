from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .filtering import SpotFilter
from .models import Spot


class SQLiteStore:
    def __init__(self, url: str) -> None:
        self.path = Path(url.removeprefix("sqlite:///"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("pragma journal_mode=WAL")
        self.conn.execute(
            "create table if not exists spots (id text primary key, timestamp_utc text not null, spotted_callsign text not null, frequency_khz real not null, source_type text not null, endpoint_name text not null, record_json text not null)"
        )
        self.conn.execute(
            "create table if not exists client_filters (callsign text primary key, filter_json text not null, updated_utc text default current_timestamp)"
        )
        self.conn.commit()

    def save_spot(self, spot: Spot) -> None:
        self.conn.execute(
            "insert or replace into spots values (?, ?, ?, ?, ?, ?, ?)",
            (
                spot.id,
                spot.timestamp_utc.isoformat(),
                spot.spotted_callsign,
                spot.frequency_khz,
                str(spot.source_type),
                spot.endpoint_name,
                json.dumps(spot.to_record(), default=str),
            ),
        )
        self.conn.commit()

    def recent(self, limit: int = 20) -> list[dict[str, object]]:
        rows = self.conn.execute(
            "select record_json from spots order by timestamp_utc desc limit ?", (limit,)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save_filter(self, callsign: str, spot_filter: SpotFilter) -> None:
        self.conn.execute(
            "insert or replace into client_filters (callsign, filter_json, updated_utc) values (?, ?, current_timestamp)",
            (callsign.upper(), json.dumps(spot_filter.to_dict(), sort_keys=True)),
        )
        self.conn.commit()

    def load_filter(self, callsign: str) -> SpotFilter | None:
        row = self.conn.execute(
            "select filter_json from client_filters where callsign = ?", (callsign.upper(),)
        ).fetchone()
        if row is None:
            return None
        return SpotFilter.from_dict(json.loads(row[0]))
