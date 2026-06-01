from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import FeedStrategy, SourceType


@dataclass(slots=True)
class EndpointConfig:
    name: str
    host: str
    port: int
    enabled: bool = True
    timeout_seconds: float = 30.0
    max_messages_per_minute: int | None = None

    @property
    def instance(self) -> str:
        return f"{self.name}/{self.host}:{self.port}"


@dataclass(slots=True)
class SourceCategoryConfig:
    source_type: SourceType
    enabled: bool = True
    strategy: FeedStrategy = FeedStrategy.ACTIVE_ACTIVE
    max_feeds: int = 10
    endpoints: list[EndpointConfig] = field(default_factory=list)


@dataclass(slots=True)
class ServerConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 7373
    banner: str = "Welcome to rbn-dxcluster"
    max_clients: int = 100
    idle_timeout_seconds: int = 1800
    client_queue_size: int = 1000


@dataclass(slots=True)
class DedupeConfig:
    enabled: bool = True
    window_seconds: int = 60
    frequency_tolerance_khz: float = 0.5


@dataclass(slots=True)
class AdminConfig:
    enabled: bool = True
    listen_host: str = "127.0.0.1"
    listen_port: int = 8080
    auth_token: str | None = None


@dataclass(slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    database_url: str = "sqlite:///data/rbn-dxcluster.sqlite3"
    upstreams: dict[SourceType, SourceCategoryConfig] = field(default_factory=dict)
    dedupe: DedupeConfig = field(default_factory=DedupeConfig)
    admin: AdminConfig = field(default_factory=AdminConfig)
    log_level: str = "INFO"


def _source_type_from_key(key: str) -> SourceType:
    normalized = key.upper()
    aliases = {
        "RBN_CW_RTTY": SourceType.RBN_CW_RTTY,
        "RBN_FT8": SourceType.RBN_FT8,
        "CLASSIC_CLUSTER": SourceType.CLASSIC_CLUSTER,
    }
    return aliases.get(normalized, SourceType(normalized))


def load_config(path: str | Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    server = ServerConfig(**raw.get("server", {}))
    dedupe = DedupeConfig(**raw.get("dedupe", {}))
    admin = AdminConfig(**raw.get("admin", {}))
    upstreams: dict[SourceType, SourceCategoryConfig] = {}
    for key, value in (raw.get("upstreams") or {}).items():
        source_type = _source_type_from_key(key)
        endpoints = [EndpointConfig(**endpoint) for endpoint in value.get("endpoints", [])]
        max_feeds = int(value.get("max_feeds", 10))
        if len(endpoints) > max_feeds:
            raise ValueError(
                f"upstream {key} defines {len(endpoints)} endpoints, above max_feeds={max_feeds}"
            )
        upstreams[source_type] = SourceCategoryConfig(
            source_type=source_type,
            enabled=bool(value.get("enabled", True)),
            strategy=FeedStrategy(value.get("strategy", FeedStrategy.ACTIVE_ACTIVE.value)),
            max_feeds=max_feeds,
            endpoints=endpoints,
        )
    return AppConfig(
        server=server,
        database_url=str(
            (raw.get("database") or {}).get("url", "sqlite:///data/rbn-dxcluster.sqlite3")
        ),
        upstreams=upstreams,
        dedupe=dedupe,
        admin=admin,
        log_level=str((raw.get("logging") or {}).get("level", "INFO")),
    )
