# Claude Code Handover Guide

This document is intended for the next coding agent or developer taking over `rbn-dxcluster`. It explains what exists, what does not exist, how the code is organised, how to validate it, and where to continue safely.

## Project summary

`rbn-dxcluster` is intended to become a self-hosted Telnet DX Cluster server for amateur radio logging software. Its core job is to ingest DX spots from multiple upstream sources, normalise them, deduplicate redundant reports, apply filters, and republish classic DX Cluster-style spot lines to Telnet clients.

The current repository is an initial scaffold plus a first functional implementation pass. It is not yet a fully production-hardened cluster node.

## Current git/project-management status

- The current environment did **not** have a GitHub remote configured.
- The current environment did **not** have `gh` available.
- Real GitHub Issues were therefore **not created**.
- `BACKLOG_TO_IMPORT.md` is the manual import source of truth for issues.
- The latest committed work added the implementation scaffold and documentation.

Before continuing in a GitHub-connected environment, import the backlog into Issues and then work issue-by-issue.

## High-level architecture

The runtime architecture is an asyncio pipeline:

1. `SourceSupervisor` manages one source category such as RBN CW/RTTY, RBN FT8, or classic cluster.
2. Each supervisor owns one or more `UpstreamConnector` instances.
3. Each connector owns one endpoint connection and writes parsed `Spot` objects to a bounded central queue.
4. `DXClusterApp._fanout()` consumes the central queue.
5. Spots are deduplicated by `SpotDeduplicator`.
6. Accepted or merged spots are persisted to SQLite by `SQLiteStore`.
7. Accepted outbound spots are broadcast to connected Telnet sessions.
8. Each Telnet session applies its own `SpotFilter` before queueing output.
9. The admin HTTP server exposes status and authenticated feed/source mutation endpoints.

## Important files and responsibilities

### `src/rbn_dxcluster/models.py`

Defines core enums and dataclasses:

- `SourceType`
- `EndpointState`
- `FeedStrategy`
- `SourceEvidence`
- `Spot`
- `EndpointMetrics`
- `EndpointStatus`

Key point: every spot should carry `source_type`, `endpoint_name`, and `source_instance`. Duplicate merges should keep supporting evidence.

### `src/rbn_dxcluster/config.py`

Loads YAML config into dataclasses. Supports source categories with:

- `enabled`
- `strategy`
- `max_feeds`
- endpoint list
- per-endpoint timeout and max message rate

Important limitation: config validation is still minimal. Add explicit validation before expanding production deployments.

### `src/rbn_dxcluster/upstream.py`

Contains `UpstreamConnector` and `SourceSupervisor`.

Current behaviour:

- Connector opens TCP connection with timeout.
- Connector reads line-by-line.
- Connector parses `DX de ...` lines.
- Connector tracks metrics in memory.
- Connector reconnects with exponential backoff on failures.
- Supervisor starts all feeds for `active_active`.
- Supervisor has a simple failover loop for non-active-active strategies.
- Supervisor exposes `enable_source`, `disable_source`, `enable_endpoint`, `disable_endpoint`, and `reconnect_endpoint`.

Important limitations:

- Failover probing is basic.
- There is no explicit endpoint-health scoring beyond current state and last message time.
- Classic cluster login/banners are not handled beyond ignoring malformed non-spot lines.

### `src/rbn_dxcluster/parsers.py`

Parses common `DX de SPOTTER: FREQ DXCALL COMMENT TIMEZ` lines.

Important limitations:

- No broad sample corpus yet.
- Real RBN/classic feeds can contain many variants.
- Add fixtures from real captured lines before changing parsing logic aggressively.

### `src/rbn_dxcluster/radio.py`

Contains radio utility helpers:

- callsign normalisation
- callsign-like validation
- frequency-to-band mapping
- mode inference

Important limitations:

- Callsign validation is deliberately pragmatic, not authoritative.
- Mode inference is heuristic.
- Band plan boundaries may need regional refinement.

### `src/rbn_dxcluster/dedupe.py`

Deduplicates spots using:

- spotted callsign
- frequency bucket
- band
- mode
- time window

Important limitation: this is simple and useful for redundant feeds, but not a sophisticated confidence/quorum engine.

### `src/rbn_dxcluster/filtering.py`

Defines `SpotFilter` and filter serialisation.

Current filters include:

- bands
- modes
- sources
- include/exclude skimmer
- include/exclude human
- min SNR
- callsign regex include/exclude
- spotter regex include/exclude
- nodupes flag

### `src/rbn_dxcluster/telnet.py`

Line-oriented TCP/Telnet-ish DX Cluster server.

Current commands include:

- `help`
- `bye` / `quit` / `exit`
- `show/dx` / `sh/dx`
- `set/filter`
- `show/filter`
- `clear/filter`
- `set/band`
- `set/mode`
- `set/source`
- `set/nodupes`
- `set/skimmer`
- `unset/skimmer`
- `set/human`
- `unset/human`
- `set/ve7cc-compatible on/off`
- `who`
- `show/version`
- `show/sources`
- `show/upstreams`

Important limitations:

- No Telnet option negotiation.
- Command compatibility is pragmatic only.
- `show/dx` does not yet query stored historical spots; it only explains live streaming.
- Rate limiting is mostly via bounded queues and max clients.

### `src/rbn_dxcluster/storage.py`

SQLite persistence for:

- spot records as JSON blobs
- per-callsign filters

Important limitations:

- No explicit schema migration system.
- No session history table yet.
- No upstream status table yet.
- No metrics table yet.
- No admin audit log table yet.

### `src/rbn_dxcluster/admin.py`

Minimal asyncio HTTP server for:

- `GET /health`
- `GET /sources`
- `GET /status`
- `POST /admin/enable-source?source=RBN_CW_RTTY`
- `POST /admin/disable-source?source=RBN_CW_RTTY`
- `POST /admin/enable-feed?endpoint=rbn-main`
- `POST /admin/disable-feed?endpoint=rbn-main`
- `POST /admin/reconnect-feed?endpoint=rbn-main`

Mutating endpoints require `admin.auth_token` and either:

- `X-Admin-Token: <token>`
- `Authorization: Bearer <token>`

Important limitations:

- No TLS.
- No user model.
- No audit persistence.
- No request body parsing.
- It should remain bound to localhost unless fronted by a secure reverse proxy.

### `src/rbn_dxcluster/app.py`

Application orchestrator. Wires config, storage, Telnet, admin, supervisors, fanout, dedupe, and signal handling.

### `src/rbn_dxcluster/cli.py`

Console entrypoint:

```bash
rbn-dxcluster serve --config config/config.example.yaml
```

## Configuration notes

The example config is `config/config.example.yaml`.

Important fields:

- `server.listen_host`
- `server.listen_port`
- `server.max_clients`
- `server.idle_timeout_seconds`
- `server.client_queue_size`
- `database.url`
- `upstreams.<category>.enabled`
- `upstreams.<category>.strategy`
- `upstreams.<category>.max_feeds`
- `upstreams.<category>.endpoints[]`
- `dedupe.enabled`
- `dedupe.window_seconds`
- `dedupe.frequency_tolerance_khz`
- `admin.enabled`
- `admin.listen_host`
- `admin.listen_port`
- `admin.auth_token`

## How to run locally

Recommended local development setup:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
rbn-dxcluster serve --config config/config.example.yaml
```

Then connect:

```bash
telnet localhost 7373
```

Enter a callsign such as `K1ABC` when prompted.

## How to run with Docker

On a host with a working Docker daemon:

```bash
docker compose up --build
```

Ports:

- Telnet DX Cluster: `7373/tcp`
- Admin HTTP: `127.0.0.1:8080/tcp`

## Validation checklist for the next agent

Run these before making functional changes:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest -q
mypy src/rbn_dxcluster
python -m compileall src tests
python - <<'PY'
from rbn_dxcluster.config import load_config
cfg = load_config('config/config.example.yaml')
print(cfg)
PY
```

If Docker is available:

```bash
docker compose config
docker compose build
docker compose up
```

## Manual smoke test plan

### Server start

1. Start the server with the example config.
2. Confirm the process binds to port 7373.
3. Confirm the admin server responds on localhost port 8080.

### Telnet client

1. Connect with `telnet localhost 7373`.
2. Enter a valid callsign.
3. Run `help`.
4. Run `show/version`.
5. Run `show/sources`.
6. Run `set/band 20m`.
7. Run `set/mode CW`.
8. Run `unset/skimmer`.
9. Run `show/filter`.
10. Disconnect with `bye`.

### Admin API

1. Set `admin.auth_token` in a local config copy.
2. Start the server.
3. Run `curl http://127.0.0.1:8080/health`.
4. Run `curl http://127.0.0.1:8080/sources`.
5. Run an unauthenticated mutation and confirm HTTP 401.
6. Run the same mutation with `X-Admin-Token` and confirm HTTP 202.

### Upstream test

1. Enable only one RBN endpoint first.
2. Confirm source state changes to active.
3. Confirm spot counters increase.
4. Add a second endpoint.
5. Confirm duplicate evidence is retained when repeated spots arrive.

## Known technical debt

- Replace ad hoc SQLite setup with schema migrations.
- Add proper structured JSON logging.
- Add admin audit log persistence.
- Add command-rate limiting.
- Add integration fixtures for real upstream lines.
- Add Telnet option negotiation or document that the server intentionally remains line-oriented.
- Add end-to-end tests using local fake upstream TCP servers and fake Telnet clients.
- Add better failover health probes.
- Add persistent upstream status metrics.
- Add Docker healthcheck instruction to the Dockerfile.
- Consider replacing the minimal admin HTTP implementation with a small ASGI framework only if complexity grows enough to justify the dependency.

## Suggested next PR sequence

1. Import backlog into GitHub Issues.
2. Add local fake upstream integration tests.
3. Improve parser coverage with real RBN/classic samples.
4. Add schema migrations and admin audit logging.
5. Implement historical `show/dx` backed by SQLite.
6. Improve failover probing and failback.
7. Add command-rate limiting and better abuse controls.
8. Run Docker build/runtime tests on real infrastructure and fix issues.
9. Test with actual logging applications.
10. Add optional connectors only after the core Telnet/RBN path is stable.

## Warnings for the next agent

- Do not assume this is production-ready just because tests pass.
- Do not add DXSummit/PSK/WSPR scraping without checking terms and technical feasibility.
- Do not expose the admin API publicly without a secure reverse proxy and strong token management.
- Do not remove duplicate evidence from stored spots; it is central to redundant-feed support.
- Do not make parser changes without adding regression lines.
- Do not let high-volume FT8 tests run uncontrolled against client fanout.
