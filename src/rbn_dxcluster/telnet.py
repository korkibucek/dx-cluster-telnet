from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from dataclasses import dataclass, field

from . import __version__
from .filtering import SpotFilter
from .formatting import format_spot
from .models import Spot
from .radio import is_callsign_like, normalize_callsign


@dataclass(slots=True, eq=False)
class ClientSession:
    callsign: str
    writer: asyncio.StreamWriter
    queue: asyncio.Queue[Spot]
    filter: SpotFilter = field(default_factory=SpotFilter)
    ve7cc_compatible: bool = False


class TelnetDXClusterServer:
    def __init__(
        self,
        host: str,
        port: int,
        banner: str,
        max_clients: int,
        idle_timeout: int,
        queue_size: int = 1000,
    ) -> None:
        self.host = host
        self.port = port
        self.banner = banner
        self.max_clients = max_clients
        self.idle_timeout = idle_timeout
        self.queue_size = queue_size
        self.sessions: set[ClientSession] = set()
        self._server: asyncio.base_events.Server | None = None
        self.source_status_provider: Callable[[], str] | None = None
        self.filter_loader: Callable[[str], SpotFilter | None] | None = None
        self.filter_saver: Callable[[str, SpotFilter], None] | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        await asyncio.gather(
            *(self._close_session(s) for s in list(self.sessions)), return_exceptions=True
        )

    async def broadcast(self, spot: Spot) -> int:
        sent = 0
        for session in list(self.sessions):
            if not session.filter.allows(spot):
                continue
            try:
                session.queue.put_nowait(spot)
                sent += 1
            except asyncio.QueueFull:
                with contextlib.suppress(asyncio.QueueEmpty):
                    session.queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    session.queue.put_nowait(spot)
        return sent

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        if len(self.sessions) >= self.max_clients:
            writer.write(b"Cluster full, try later\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        writer.write(b"Callsign: ")
        await writer.drain()
        raw = await asyncio.wait_for(reader.readline(), timeout=60)
        callsign = normalize_callsign(raw.decode(errors="replace"))
        if not callsign or not is_callsign_like(callsign):
            writer.write(b"Invalid callsign\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        saved_filter = self.filter_loader(callsign) if self.filter_loader else None
        session = ClientSession(
            callsign,
            writer,
            asyncio.Queue(maxsize=self.queue_size),
            saved_filter or SpotFilter(),
        )
        self.sessions.add(session)
        writer.write((self.banner + "\r\nType HELP for commands.\r\n").encode())
        await writer.drain()
        sender = asyncio.create_task(self._sender(session))
        try:
            while not reader.at_eof():
                line = await asyncio.wait_for(reader.readline(), timeout=self.idle_timeout)
                if not line:
                    break
                response = await self.execute_command(
                    session, line.decode(errors="replace").strip()
                )
                if response:
                    writer.write((response + "\r\n").encode())
                    await writer.drain()
                if response == "Bye":
                    break
        except (TimeoutError, ConnectionError):
            writer.write(b"Idle timeout or connection closed\r\n")
            with contextlib.suppress(Exception):
                await writer.drain()
        finally:
            sender.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sender
            await self._close_session(session)

    async def _sender(self, session: ClientSession) -> None:
        while True:
            spot = await session.queue.get()
            session.writer.write(
                format_spot(spot, "verbose" if session.ve7cc_compatible else "classic").encode()
            )
            await session.writer.drain()

    async def _close_session(self, session: ClientSession) -> None:
        self.sessions.discard(session)
        session.writer.close()
        with contextlib.suppress(Exception):
            await session.writer.wait_closed()

    def _save_session_filter(self, session: ClientSession) -> None:
        if self.filter_saver:
            self.filter_saver(session.callsign, session.filter)

    async def execute_command(self, session: ClientSession, command: str) -> str:
        parts = command.split()
        verb = parts[0].lower() if parts else ""
        if verb in {"bye", "quit", "exit"}:
            return "Bye"
        if verb in {"help", "?"}:
            return "Commands: help, bye, show/dx, set/filter, show/filter, clear/filter, set/band, set/mode, set/source, set/skimmer, unset/skimmer, set/human, unset/human, set/nodupes, set/ve7cc-compatible on|off, who, show/version, show/sources"
        if verb in {"who"}:
            return "Connected: " + ", ".join(sorted(s.callsign for s in self.sessions))
        if verb in {"show/version", "sh/version"}:
            return f"rbn-dxcluster {__version__}"
        if verb in {"show/sources", "show/upstreams"}:
            return (
                self.source_status_provider()
                if self.source_status_provider
                else "Source status unavailable"
            )
        if verb in {"show/filter", "sh/filter"}:
            return str(session.filter)
        if verb == "clear/filter":
            session.filter = SpotFilter()
            self._save_session_filter(session)
            return "Filters cleared"
        if verb == "set/band" and len(parts) > 1:
            session.filter.bands = {p.lower() for p in parts[1:]}
            self._save_session_filter(session)
            return "Band filter updated"
        if verb == "set/mode" and len(parts) > 1:
            session.filter.modes = {p.upper() for p in parts[1:]}
            self._save_session_filter(session)
            return "Mode filter updated"
        if verb == "set/source" and len(parts) > 1:
            session.filter.sources = {p.upper() for p in parts[1:]}
            self._save_session_filter(session)
            return "Source filter updated"
        if verb == "set/skimmer":
            session.filter.include_skimmer = True
            self._save_session_filter(session)
            return "Skimmer spots enabled"
        if verb == "unset/skimmer":
            session.filter.include_skimmer = False
            self._save_session_filter(session)
            return "Skimmer spots disabled"
        if verb == "set/human":
            session.filter.include_human = True
            self._save_session_filter(session)
            return "Human spots enabled"
        if verb == "unset/human":
            session.filter.include_human = False
            self._save_session_filter(session)
            return "Human spots disabled"
        if verb == "set/nodupes":
            session.filter.nodupes = True
            self._save_session_filter(session)
            return "Duplicate suppression enabled"
        if verb == "set/ve7cc-compatible" and len(parts) > 1:
            session.ve7cc_compatible = parts[1].lower() in {"on", "true", "1", "yes"}
            return "VE7CC compatibility updated"
        if verb in {"show/dx", "sh/dx"}:
            return "Live DX spots stream automatically as they arrive."
        if verb == "set/filter":
            return "Use set/band, set/mode, set/source, set/skimmer/unset/skimmer, set/human/unset/human."
        return "Unknown command. Type HELP."
