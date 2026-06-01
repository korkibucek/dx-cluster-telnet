from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from .config import EndpointConfig, SourceCategoryConfig
from .models import EndpointMetrics, EndpointState, EndpointStatus, FeedStrategy, SourceType, Spot
from .parsers import parse_spot_line

LOGGER = logging.getLogger(__name__)
SpotSink = Callable[[Spot], asyncio.Future[None] | None]


class UpstreamConnector:
    def __init__(
        self, source_type: SourceType, endpoint: EndpointConfig, output: asyncio.Queue[Spot]
    ) -> None:
        self.source_type = source_type
        self.endpoint = endpoint
        self.output = output
        self.metrics = EndpointMetrics(state=EndpointState.DISABLED)
        self._enabled = endpoint.enabled
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        if self.metrics.state == EndpointState.DISABLED:
            self.metrics.state = EndpointState.RECONNECTING

    def disable(self) -> None:
        self._enabled = False
        self.metrics.state = EndpointState.DISABLED

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self.run(), name=f"feed:{self.endpoint.name}")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            if not self._enabled:
                self.metrics.state = EndpointState.DISABLED
                await asyncio.sleep(1)
                continue
            self.metrics.state = EndpointState.RECONNECTING
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.endpoint.host, self.endpoint.port),
                    timeout=self.endpoint.timeout_seconds,
                )
                LOGGER.info(
                    "connected upstream",
                    extra={"endpoint": self.endpoint.name, "source_type": str(self.source_type)},
                )
                self.metrics.state = EndpointState.ACTIVE
                backoff = 1.0
                await self._read_loop(reader)
                writer.close()
                await writer.wait_closed()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - connector must survive unreliable feeds
                self.metrics.reconnect_count += 1
                self.metrics.state = EndpointState.FAILED
                LOGGER.warning(
                    "upstream connection failed: %s", exc, extra={"endpoint": self.endpoint.name}
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        while not self._stop.is_set() and self._enabled:
            line = await asyncio.wait_for(reader.readline(), timeout=self.endpoint.timeout_seconds)
            if not line:
                raise ConnectionError("upstream closed connection")
            now = datetime.now(UTC)
            if (
                self.endpoint.max_messages_per_minute is not None
                and self.metrics.messages_per_minute >= self.endpoint.max_messages_per_minute
            ):
                continue
            text = line.decode(errors="replace").rstrip("\r\n")
            spot = parse_spot_line(
                text, self.source_type, self.endpoint.name, self.endpoint.instance
            )
            if spot is None:
                self.metrics.parse_errors += 1
                continue
            self.metrics.mark_message(now)
            try:
                self.output.put_nowait(spot)
            except asyncio.QueueFull:
                LOGGER.warning(
                    "central spot queue full, dropping spot", extra={"endpoint": self.endpoint.name}
                )

    def status(self) -> EndpointStatus:
        return EndpointStatus(
            category=self.source_type,
            name=self.endpoint.name,
            host=self.endpoint.host,
            port=self.endpoint.port,
            state=self.metrics.state,
            spots_per_minute=self.metrics.messages_per_minute,
            last_message_utc=self.metrics.last_message_utc,
            reconnects=self.metrics.reconnect_count,
            spots_received=self.metrics.spots_received,
            parse_errors=self.metrics.parse_errors,
            enabled=self._enabled,
        )


class SourceSupervisor:
    def __init__(self, config: SourceCategoryConfig, output: asyncio.Queue[Spot]) -> None:
        self.config = config
        self.output = output
        self.connectors = [
            UpstreamConnector(config.source_type, endpoint, output)
            for endpoint in config.endpoints[: config.max_feeds]
        ]
        self._source_enabled = config.enabled
        self._strategy_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._source_enabled:
            return
        if self.config.strategy == FeedStrategy.ACTIVE_ACTIVE:
            for connector in self.connectors:
                connector.start()
        else:
            self._strategy_task = asyncio.create_task(
                self._run_failover(), name=f"supervisor:{self.config.source_type}"
            )

    async def stop(self) -> None:
        if self._strategy_task:
            self._strategy_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._strategy_task
        await asyncio.gather(
            *(connector.stop() for connector in self.connectors), return_exceptions=True
        )

    async def _run_failover(self) -> None:
        while True:
            enabled = [c for c in self.connectors if c.enabled]
            if not enabled:
                await asyncio.sleep(5)
                continue
            active = next((c for c in enabled if c.metrics.state == EndpointState.ACTIVE), None)
            preferred = enabled[0]
            target = (
                preferred
                if self.config.strategy == FeedStrategy.PRIORITY_FAILOVER
                else (active or preferred)
            )
            for connector in self.connectors:
                if connector is target:
                    connector.start()
                elif (
                    self.config.strategy == FeedStrategy.PRIORITY_FAILOVER
                    and connector.metrics.state == EndpointState.ACTIVE
                ):
                    await connector.stop()
                    connector.metrics.state = EndpointState.STANDBY
            await asyncio.sleep(10)

    def enable_source(self) -> None:
        self._source_enabled = True
        self.config.enabled = True
        self.start()

    async def disable_source(self) -> None:
        self._source_enabled = False
        self.config.enabled = False
        await asyncio.gather(
            *(connector.stop() for connector in self.connectors), return_exceptions=True
        )
        for connector in self.connectors:
            connector.metrics.state = EndpointState.DISABLED

    def enable_endpoint(self, name: str) -> bool:
        for connector in self.connectors:
            if connector.endpoint.name == name:
                connector.enable()
                connector.start()
                return True
        return False

    async def disable_endpoint(self, name: str) -> bool:
        for connector in self.connectors:
            if connector.endpoint.name == name:
                connector.disable()
                await connector.stop()
                return True
        return False

    async def reconnect_endpoint(self, name: str) -> bool:
        for connector in self.connectors:
            if connector.endpoint.name == name:
                await connector.stop()
                connector.enable()
                connector.start()
                return True
        return False

    def statuses(self) -> list[EndpointStatus]:
        return [connector.status() for connector in self.connectors]

    def status_text(self) -> str:
        statuses = self.statuses()
        healthy = sum(1 for status in statuses if status.state == EndpointState.ACTIVE)
        lines = [
            f"Source category: {self.config.source_type}",
            f"Strategy: {self.config.strategy}",
            f"Enabled: {'yes' if self._source_enabled else 'no'}",
            f"Healthy feeds: {healthy}/{len(statuses)}",
            "Endpoint                  State         Spots/min   Last message UTC       Reconnects",
        ]
        for status in statuses:
            last = (
                status.last_message_utc.strftime("%Y-%m-%d %H:%M:%S")
                if status.last_message_utc
                else "never"
            )
            lines.append(
                f"{status.name:<25} {status.state:<13} {status.spots_per_minute:<11.0f} {last:<22} {status.reconnects}"
            )
        return "\n".join(lines)
