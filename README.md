# rbn-dxcluster

`rbn-dxcluster` is a self-hosted, line-oriented Telnet DX Cluster server for amateur radio logging programs. It ingests spots from redundant upstream feeds such as Reverse Beacon Network CW/RTTY, Reverse Beacon Network FT8, and classic DX Cluster nodes, normalises them into a common spot model, suppresses duplicates, applies per-client filters, and republishes DX Cluster-compatible lines.

## Key features

- Async Python 3.12 Telnet server using classic `DX de SPOTTER: FREQ DXCALL COMMENT TIMEZ` output.
- Multiple redundant endpoints per source category, up to `max_feeds` (default 10).
- Feed strategies: `active_active`, `active_passive`, and `priority_failover` foundation.
- Per-endpoint state, health, reconnect counters, parse errors, last-message time, and rate limiting.
- Normalised `Spot` model with endpoint evidence via `duplicate_sources`/`supporting_sources`.
- Duplicate suppression across redundant feeds with confidence-score uplift when independent endpoints report the same spot.
- Per-client Telnet commands for band, mode, source, human/skimmer, duplicate, and compatibility settings.
- SQLite persistence by default.
- Localhost-bound admin HTTP status endpoints.
- Docker and Docker Compose runtime.

## Quick start

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
rbn-dxcluster serve --config config/config.example.yaml
```

Connect with telnet or your logger:

```bash
telnet localhost 7373
```

When prompted, enter your callsign. Live spots stream automatically.

## Docker Compose

```bash
docker compose up --build
```

The Telnet server listens on `localhost:7373`; the admin API is published only on `127.0.0.1:8080`.

## Common Telnet commands

```text
help
show/version
show/sources
set/band 20m
set/mode CW
unset/skimmer
set/human
show/filter
clear/filter
bye
```

To receive only CW spots on 20m:

```text
set/band 20m
set/mode CW
```

To suppress RBN/skimmer spots and show only human classic-cluster spots:

```text
unset/skimmer
set/human
```


## Admin feed control

Read-only admin status is available locally:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/sources
curl http://127.0.0.1:8080/status
```

Mutating actions require `admin.auth_token` in the YAML config and an `X-Admin-Token` or Bearer token header:

```bash
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/disable-feed?endpoint=rbn-main'
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/reconnect-feed?endpoint=rbn-main'
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/disable-source?source=RBN_CW_RTTY'
```

## Configuration

Edit `config/config.example.yaml`. Each source category has a strategy and a list of endpoints:

```yaml
upstreams:
  rbn_cw_rtty:
    enabled: true
    strategy: active_active
    max_feeds: 10
    endpoints:
      - name: rbn-main
        host: telnet.reversebeacon.net
        port: 7000
```

See [CONFIGURATION.md](CONFIGURATION.md) and [SOURCES.md](SOURCES.md) for details.

## Project management / backlog

Real GitHub Issues were not created from the agent environment because the checkout had no configured GitHub remote and no GitHub CLI. Use `BACKLOG_TO_IMPORT.md` as the import-ready backlog, then make GitHub Issues the canonical tracker once the repository is connected to GitHub. See `docs/DISCOVERY.md`, `docs/PROJECT_STATUS.md`, and `docs/HANDOVER.md` before continuing major development.

## Caveats

RBN feeds are high-volume by design. Keep deduplication enabled, set endpoint `max_messages_per_minute` for noisy feeds, and prefer client filters when using consumer logging software. FT8 RBN spots are skimmer-originated reports, not human DX Cluster spots, and are marked accordingly.

## Documentation

- [INSTALL.md](INSTALL.md)
- [CONFIGURATION.md](CONFIGURATION.md)
- [COMMANDS.md](COMMANDS.md)
- [SOURCES.md](SOURCES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Operations](docs/OPERATIONS.md)
- [Security](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Discovery Report](docs/DISCOVERY.md)
- [Project Status](docs/PROJECT_STATUS.md)
- [Claude Code Handover](docs/HANDOVER.md)

## Testing

```bash
pytest
ruff check .
python -m compileall src tests
```
