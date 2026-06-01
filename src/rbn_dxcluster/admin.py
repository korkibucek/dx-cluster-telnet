from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True, slots=True)
class AdminRequest:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]


class AdminServer:
    def __init__(
        self,
        host: str,
        port: int,
        status_provider: Callable[[], dict[str, object]],
        text_provider: Callable[[], str],
        action_handler: Callable[[str, dict[str, str]], Awaitable[tuple[int, dict[str, object]]]],
        auth_token: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.status_provider = status_provider
        self.text_provider = text_provider
        self.action_handler = action_handler
        self.auth_token = auth_token
        self._server: asyncio.base_events.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request = await self._read_request(reader)
        if request is None:
            await self._send(writer, 400, b"bad request\n", "text/plain")
            return

        if request.method == "GET" and request.path in {"/health", "/"}:
            await self._send_json(writer, 200, {"status": "ok"})
        elif request.method == "GET" and request.path == "/sources":
            await self._send(writer, 200, (self.text_provider() + "\n").encode(), "text/plain")
        elif request.method == "GET" and request.path == "/status":
            await self._send_json(writer, 200, self.status_provider())
        elif request.method == "POST" and request.path.startswith("/admin/"):
            if not self._authorized(request):
                await self._send_json(writer, 401, {"error": "admin token required"})
                return
            status, payload = await self.action_handler(
                request.path.removeprefix("/admin/"), self._query_params(request)
            )
            await self._send_json(writer, status, payload)
        else:
            await self._send(writer, 404, b"not found\n", "text/plain")

    async def _read_request(self, reader: asyncio.StreamReader) -> AdminRequest | None:
        request_line = await reader.readline()
        if not request_line:
            return None
        parts = request_line.decode(errors="replace").strip().split()
        if len(parts) < 2:
            return None
        method, target = parts[0].upper(), parts[1]
        parsed = urlsplit(target)
        headers: dict[str, str] = {}
        while True:
            line = await reader.readline()
            if line in {b"\r\n", b"\n", b""}:
                break
            name, _, value = line.decode(errors="replace").partition(":")
            if name:
                headers[name.strip().lower()] = value.strip()
        return AdminRequest(method, parsed.path, parse_qs(parsed.query), headers)

    def _authorized(self, request: AdminRequest) -> bool:
        if not self.auth_token:
            return False
        expected = f"Bearer {self.auth_token}"
        return (
            request.headers.get("authorization") == expected
            or request.headers.get("x-admin-token") == self.auth_token
        )

    @staticmethod
    def _query_params(request: AdminRequest) -> dict[str, str]:
        return {key: values[-1] for key, values in request.query.items() if values}

    async def _send_json(
        self, writer: asyncio.StreamWriter, status: int, payload: dict[str, object]
    ) -> None:
        body = (json.dumps(payload, default=str, indent=2) + "\n").encode()
        await self._send(writer, status, body, "application/json")

    async def _send(
        self, writer: asyncio.StreamWriter, status: int, body: bytes, content_type: str
    ) -> None:
        reason = {
            200: "OK",
            202: "Accepted",
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found",
        }.get(status, "OK")
        writer.write(f"HTTP/1.1 {status} {reason}\r\n".encode())
        writer.write(
            f"Content-Type: {content_type}\r\nContent-Length: {len(body)}\r\n\r\n".encode()
        )
        writer.write(body)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
