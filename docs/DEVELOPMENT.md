# Development

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

## Checks

```bash
pytest
ruff check .
python -m compileall src tests
```

## Repository discovery report

The repository initially contained only a minimal `README.md` and no source, tests, packaging, deployment, or issue backlog. The requested Telnet DX Cluster application is technically viable with Python asyncio and SQLite. The highest risks are upstream feed volume, imperfect compatibility across DX Cluster dialects, and future API/terms constraints for optional web-derived sources.


## Handover documents

Before continuing development, read:

- `docs/DISCOVERY.md` for repository discovery and viability notes.
- `docs/PROJECT_STATUS.md` for current production-readiness status.
- `docs/HANDOVER.md` for module-by-module guidance and next-agent instructions.
- `BACKLOG_TO_IMPORT.md` for the manual GitHub Issue import backlog.

## GitHub Issues note

Real GitHub Issues were not created by the agent because this local checkout had no GitHub remote and no GitHub CLI available. Import `BACKLOG_TO_IMPORT.md` manually once the project is connected to GitHub.
