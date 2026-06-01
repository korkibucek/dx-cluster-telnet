from __future__ import annotations

import asyncio
import logging
import signal
from collections import Counter

from .admin import AdminServer
from .config import AppConfig
from .dedupe import SpotDeduplicator
from .models import Spot
from .storage import SQLiteStore
from .telnet import TelnetDXClusterServer
from .upstream import SourceSupervisor

LOGGER = logging.getLogger(__name__)


class DXClusterApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.queue: asyncio.Queue[Spot] = asyncio.Queue(maxsize=10000)
        self.dedupe = SpotDeduplicator(
            config.dedupe.window_seconds, config.dedupe.frequency_tolerance_khz
        )
        self.store = SQLiteStore(config.database_url)
        self.telnet = TelnetDXClusterServer(
            config.server.listen_host,
            config.server.listen_port,
            config.server.banner,
            config.server.max_clients,
            config.server.idle_timeout_seconds,
            config.server.client_queue_size,
        )
        self.supervisors = [
            SourceSupervisor(upstream, self.queue) for upstream in config.upstreams.values()
        ]
        self.telnet.source_status_provider = self.sources_text
        self.telnet.filter_loader = self.store.load_filter
        self.telnet.filter_saver = self.store.save_filter
        self.admin = (
            AdminServer(
                config.admin.listen_host,
                config.admin.listen_port,
                self.status,
                self.sources_text,
                self.handle_admin_action,
                config.admin.auth_token,
            )
            if config.admin.enabled
            else None
        )
        self.counters: Counter[str] = Counter()
        self._fanout_task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def run(self) -> None:
        await self.telnet.start()
        if self.admin:
            await self.admin.start()
        for supervisor in self.supervisors:
            supervisor.start()
        self._fanout_task = asyncio.create_task(self._fanout(), name="spot-fanout")
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._stop.set)
        await self._stop.wait()
        await self.stop()

    async def stop(self) -> None:
        if self._fanout_task:
            self._fanout_task.cancel()
        await asyncio.gather(
            *(supervisor.stop() for supervisor in self.supervisors), return_exceptions=True
        )
        await self.telnet.stop()
        if self.admin:
            await self.admin.stop()

    async def _fanout(self) -> None:
        while True:
            spot = await self.queue.get()
            self.counters[f"received.{spot.endpoint_name}"] += 1
            if self.config.dedupe.enabled:
                should_emit, merged = self.dedupe.process(spot)
                if not should_emit:
                    self.counters["deduplicated"] += 1
                    self.store.save_spot(merged)
                    continue
                spot = merged
            self.store.save_spot(spot)
            sent = await self.telnet.broadcast(spot)
            self.counters["sent_to_clients"] += sent

    def _find_supervisor(self, source_category: str) -> SourceSupervisor | None:
        wanted = source_category.upper()
        for supervisor in self.supervisors:
            if str(supervisor.config.source_type).upper() == wanted:
                return supervisor
        return None

    def _find_endpoint_supervisor(self, endpoint_name: str) -> SourceSupervisor | None:
        for supervisor in self.supervisors:
            if any(connector.endpoint.name == endpoint_name for connector in supervisor.connectors):
                return supervisor
        return None

    async def handle_admin_action(
        self, action: str, params: dict[str, str]
    ) -> tuple[int, dict[str, object]]:
        if action in {"enable-source", "disable-source"}:
            category = params.get("source") or params.get("category")
            if not category:
                return 400, {"error": "source parameter required"}
            supervisor = self._find_supervisor(category)
            if supervisor is None:
                return 404, {"error": f"unknown source category {category}"}
            if action == "enable-source":
                supervisor.enable_source()
            else:
                await supervisor.disable_source()
            return 202, {"status": "ok", "action": action, "source": category}

        if action in {"enable-feed", "disable-feed", "reconnect-feed"}:
            endpoint = params.get("endpoint") or params.get("feed")
            if not endpoint:
                return 400, {"error": "endpoint parameter required"}
            supervisor = self._find_endpoint_supervisor(endpoint)
            if supervisor is None:
                return 404, {"error": f"unknown endpoint {endpoint}"}
            if action == "enable-feed":
                ok = supervisor.enable_endpoint(endpoint)
            elif action == "disable-feed":
                ok = await supervisor.disable_endpoint(endpoint)
            else:
                ok = await supervisor.reconnect_endpoint(endpoint)
            if not ok:
                return 404, {"error": f"unknown endpoint {endpoint}"}
            return 202, {"status": "ok", "action": action, "endpoint": endpoint}

        return 404, {"error": f"unknown admin action {action}"}

    def sources_text(self) -> str:
        return (
            "\n\n".join(supervisor.status_text() for supervisor in self.supervisors)
            or "No upstreams configured"
        )

    def status(self) -> dict[str, object]:
        return {
            "clients": len(self.telnet.sessions),
            "counters": dict(self.counters),
            "dedupe": {"accepted": self.dedupe.accepted, "duplicates": self.dedupe.duplicates},
            "sources": [
                [status.__dict__ for status in supervisor.statuses()]
                for supervisor in self.supervisors
            ],
        }
