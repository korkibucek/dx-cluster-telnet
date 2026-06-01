# Repository Discovery Report

## Discovery date

This discovery report was prepared during the initial project scaffold and expanded for handover after the first implementation pass.

## Repository state before implementation

The repository initially contained only a minimal root `README.md` with the project/repository name. There was no application package, no tests, no packaging metadata, no Docker runtime, no CI workflow, no deployment scripts, no configuration example, no architecture documentation, and no existing GitHub Issues available from the local checkout.

## GitHub access / issue management finding

Real GitHub Issues were **not** created from this environment because the checkout has no configured Git remote and no GitHub CLI (`gh`) available. This means there is no authenticated GitHub repository target for issue creation, labels, milestones, or project-board updates from the agent environment.

The repository therefore includes `BACKLOG_TO_IMPORT.md` as the canonical manual-import backlog. It is written in an issue-import style with summaries, background, proposed work, acceptance criteria, technical notes, priority, and suggested labels.

Recommended handover action:

1. Add the GitHub remote in the developer environment.
2. Review `BACKLOG_TO_IMPORT.md`.
3. Create labels listed in the backlog if they do not already exist.
4. Import each backlog entry as a GitHub Issue.
5. Link future pull requests to the imported issue numbers.

## Implemented project assets

The repository now contains:

- Python package source under `src/rbn_dxcluster/`.
- Unit/integration tests under `tests/`.
- Project packaging in `pyproject.toml`.
- Example YAML configuration in `config/config.example.yaml`.
- Docker and Docker Compose runtime artifacts.
- Deployment helper scripts under `deploy/`.
- CI workflow under `.github/workflows/ci.yml`.
- User/developer/operations/security/architecture documentation.
- Manual issue backlog in `BACKLOG_TO_IMPORT.md`.

## Current application capabilities

The current scaffold provides a working core architecture for:

- Telnet DX Cluster-compatible client sessions.
- Callsign prompt and basic callsign validation.
- Live spot broadcast to multiple clients with bounded queues.
- Per-session filtering by band, mode, source category, human/skimmer flags, and duplicate settings.
- Filter persistence keyed by callsign in SQLite.
- RBN CW/RTTY, RBN FT8, and classic cluster-style line parsing for `DX de ...` lines.
- Multiple endpoints per source category.
- Independent endpoint state, reconnect/backoff loop, timeout, parse-error metrics, message counters, and endpoint rate limiting.
- Source supervision for active-active and failover-oriented strategies.
- Duplicate suppression across redundant feeds with supporting-source evidence retention.
- SQLite persistence for recent spots and per-callsign filters.
- Localhost admin status endpoints.
- Authenticated admin mutation endpoints for source/feed control.

## What appears complete enough for the first scaffold

The following areas are implemented well enough for an initial handover scaffold:

- Package layout and CLI entrypoint.
- Config loading for the expected source-category shape.
- Core data model fields requested by the project brief.
- Basic RBN/classic cluster parsing.
- Async endpoint connection lifecycle.
- Active-active redundant endpoint startup.
- Duplicate merging with endpoint evidence.
- Telnet command parsing for common commands.
- SQLite table creation and basic persistence.
- Dockerfile and Compose file.
- CI workflow for lint/test/compile checks.
- Foundational documentation.

## What is intentionally incomplete

The current implementation is a scaffold, not a finished production DX Cluster. Important gaps remain:

- No full Telnet option negotiation; the implementation uses newline-oriented TCP streams.
- No comprehensive DXSpider/CC Cluster command compatibility.
- No country/DXCC lookup.
- No PostgreSQL backend despite architectural allowance.
- No complete quorum/merge confidence engine beyond supporting-source evidence and simple confidence uplift.
- No DXSummit, PSK Reporter, WSPRnet, or local skimmer connectors.
- No active health probes for higher-priority failback.
- No persisted upstream status/metrics tables beyond current in-memory metrics.
- No audit log table for admin mutations.
- No rate limiting of inbound client commands beyond output queue bounds and idle timeout.
- No full end-to-end live upstream integration test.
- No Docker runtime smoke test in this environment.
- No production systemd unit files.
- No release automation.

## Risks

### RBN volume

RBN and FT8 feeds can be extremely high volume. The code uses bounded queues and per-endpoint message-rate limits, but production deployments still need load testing, realistic filtering defaults, and careful memory/CPU observation.

### Spot format variability

Classic cluster nodes and skimmer feeds may differ in banner text, login prompts, line formats, comments, timestamp positioning, and frequency formatting. The parser currently handles common `DX de ...` lines but should be expanded with captured real-world samples.

### Telnet compatibility

Many logging programs work with simple line-oriented DX Cluster TCP sessions, but some expect Telnet option negotiation or specific DXSpider/CC Cluster command responses. Compatibility testing with target logging programs is required.

### Admin security

The admin API is intentionally localhost-bound by default. Mutating endpoints require a token when configured, but there is no user model, no TLS in-process, and no built-in brute-force protection. Keep it behind localhost or a protected reverse proxy.

### Data model evolution

The `Spot` model includes many nullable fields for future enrichment. Schema migrations are not yet implemented. If the SQLite schema evolves, add explicit migrations rather than ad hoc `CREATE TABLE` statements.

## Recommended next steps

1. Import `BACKLOG_TO_IMPORT.md` into GitHub Issues.
2. Create labels: `foundation`, `docs`, `tests`, `telnet`, `upstream`, `dedupe`, `storage`, `admin`, `security`, `deployment`, `observability`, `connector`, `compatibility`, `operations`.
3. Run the test suite from a clean clone.
4. Run a local no-upstream server smoke test.
5. Run Docker/Compose build and runtime smoke tests on a host with a working Docker daemon.
6. Test with one real RBN feed and one classic cluster feed.
7. Capture real upstream line samples and add parser regression tests.
8. Prioritise the issues marked `High` in `BACKLOG_TO_IMPORT.md`.
