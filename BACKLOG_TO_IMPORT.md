# Backlog Import Notes

Real GitHub Issues were not created from the agent environment because the local checkout had no configured GitHub remote and no `gh` CLI. Import the issues below manually into GitHub. Suggested labels are included per issue.

---

# Issue: Import and triage this backlog in GitHub Issues

## Summary
Create real GitHub Issues from this backlog file and make GitHub Issues the canonical project-management system.

## Background
The project instructions required GitHub Issues, but the local environment had no GitHub remote or CLI access. This file is the fallback backlog and must be imported before ongoing work continues.

## Proposed Work
- Create the suggested labels if they do not already exist.
- Create one GitHub Issue for each backlog entry below.
- Preserve priorities and acceptance criteria.
- Add milestones if useful.
- Link future PRs to imported issue numbers.
- Replace this file with a note pointing to GitHub Issues after import.

## Acceptance Criteria
- All backlog entries are represented as GitHub Issues.
- Labels exist and are applied consistently.
- Each issue has clear acceptance criteria.
- README or docs link to the GitHub Issues location.

## Technical Notes
Suggested labels: `foundation`, `docs`, `tests`, `telnet`, `upstream`, `dedupe`, `storage`, `admin`, `security`, `deployment`, `observability`, `connector`, `compatibility`, `operations`, `bug`, `enhancement`, `high-priority`.

## Priority
High

## Labels
foundation, docs, high-priority

---

# Issue: Run Docker build and Compose runtime smoke tests

## Summary
Validate that the Dockerfile and Docker Compose setup build and run on a host with a working Docker daemon.

## Background
The agent environment could not reliably run Docker daemon-backed build/runtime tests. The files exist, but they require real validation.

## Proposed Work
- Run `docker compose config`.
- Run `docker compose build`.
- Run `docker compose up`.
- Confirm Telnet port `7373` is reachable.
- Confirm admin health endpoint responds on `127.0.0.1:8080`.
- Fix any image, permission, user, volume, or networking issues.
- Document observed output in `docs/DEPLOYMENT.md`.

## Acceptance Criteria
- `docker compose build` succeeds.
- `docker compose up` starts the service.
- `curl http://127.0.0.1:8080/health` returns healthy JSON.
- A Telnet client can connect to port `7373` and receive the callsign prompt.
- Any required Docker troubleshooting notes are documented.

## Technical Notes
Relevant files: `Dockerfile`, `docker-compose.yml`, `deploy/healthcheck.sh`, `docs/DEPLOYMENT.md`.

## Priority
High

## Labels
deployment, tests, high-priority

---

# Issue: Add fake upstream integration tests

## Summary
Add end-to-end asyncio tests using local fake upstream TCP servers to verify ingestion, dedupe, persistence, and Telnet fanout together.

## Background
Current tests are mostly unit-level. The highest-risk path is the async pipeline across upstream connectors, central queue, dedupe, storage, and Telnet sessions.

## Proposed Work
- Build test helpers for fake upstream TCP servers.
- Emit valid and malformed `DX de ...` lines.
- Start `DXClusterApp` or its components with local endpoints.
- Connect a fake Telnet client.
- Assert accepted spots reach the client.
- Assert malformed lines increment parse errors without crashing.
- Assert duplicate lines from two endpoints emit only once.
- Assert supporting-source evidence is stored.

## Acceptance Criteria
- Tests cover active-active ingestion from two fake endpoints.
- Tests cover reconnect after fake upstream disconnect.
- Tests cover malformed line handling.
- Tests cover duplicate merge across fake endpoints.
- Tests run without external network access.

## Technical Notes
Relevant modules: `upstream.py`, `app.py`, `dedupe.py`, `telnet.py`, `storage.py`.

## Priority
High

## Labels
tests, upstream, telnet, dedupe, high-priority

---

# Issue: Expand parser fixtures with real RBN and classic cluster samples

## Summary
Collect representative live lines from RBN CW/RTTY, RBN FT8, and classic cluster nodes and add parser regression tests.

## Background
Spot source formats vary. Parser correctness is central to reliability.

## Proposed Work
- Capture sample non-secret lines from RBN CW/RTTY.
- Capture sample non-secret lines from RBN FT8.
- Capture sample lines from one or more classic cluster nodes.
- Include malformed/banner/login lines.
- Add fixtures under `tests/fixtures/`.
- Add tests for expected parse results and expected rejects.
- Document parsing assumptions in `SOURCES.md`.

## Acceptance Criteria
- At least 20 valid RBN CW/RTTY samples are tested.
- At least 20 valid RBN FT8 samples are tested.
- At least 20 valid classic cluster samples are tested.
- At least 10 malformed/banner lines are tested as rejects.
- Parser changes are regression-protected.

## Technical Notes
Relevant modules: `parsers.py`, `radio.py`, `tests/test_radio_parsing.py`.

## Priority
High

## Labels
upstream, tests, compatibility, high-priority

---

# Issue: Implement historical `show/dx` backed by SQLite

## Summary
Make `show/dx` and `sh/dx` return recent stored spots that match the current session filter instead of only explaining that live streaming is automatic.

## Background
Classic DX Cluster users expect `show/dx` to display recent spots.

## Proposed Work
- Add typed spot rehydration or query helpers to `SQLiteStore`.
- Add a recent-spots command path in `TelnetDXClusterServer`.
- Apply the current session filter to historical results.
- Format historical results with the existing formatter.
- Add tests for filtered history output.

## Acceptance Criteria
- `show/dx` returns recent spots when present.
- `sh/dx` is an alias.
- Session filters are applied to historical output.
- Empty history returns a helpful message.
- Tests cover matching and non-matching filters.

## Technical Notes
Relevant modules: `telnet.py`, `storage.py`, `formatting.py`, `filtering.py`.

## Priority
High

## Labels
telnet, storage, compatibility

---

# Issue: Add SQLite schema migrations

## Summary
Replace ad hoc table creation with a simple migration system for SQLite schema changes.

## Background
The schema already includes spots and client filters. Future operational metrics, upstream status, and audit logs will require controlled schema evolution.

## Proposed Work
- Add a `schema_migrations` table.
- Define ordered migration statements in code or SQL files.
- Migrate existing `spots` and `client_filters` creation into versioned migrations.
- Add tests for fresh database and already-current database.
- Document migration behaviour.

## Acceptance Criteria
- Fresh database initialises successfully.
- Re-running startup is idempotent.
- Migration version is recorded.
- Tests cover migration idempotency.

## Technical Notes
Relevant module: `storage.py`.

## Priority
High

## Labels
storage, operations, high-priority

---

# Issue: Add admin audit logging

## Summary
Persist all mutating admin actions with timestamp, action, target, result, and request metadata.

## Background
The admin API can enable/disable feeds and sources. Production operation needs accountability.

## Proposed Work
- Add an `admin_audit_log` table.
- Record action, parameters, HTTP status, remote address if available, and timestamp.
- Avoid storing secret token values.
- Add tests for successful and failed mutations.
- Document audit log location and retention.

## Acceptance Criteria
- Successful admin mutations are logged.
- Failed admin mutations are logged where practical.
- Tokens are never stored.
- Tests verify audit rows are written.

## Technical Notes
Relevant modules: `admin.py`, `app.py`, `storage.py`.

## Priority
High

## Labels
admin, security, storage, operations

---

# Issue: Improve source failover health probing and failback

## Summary
Implement robust active-passive and priority-failover health probes with periodic failback to higher-priority endpoints.

## Background
The current failover loop is a foundation, not complete production-grade failover.

## Proposed Work
- Define health criteria using connection state and last message timestamp.
- Add probe attempts for higher-priority endpoints without disrupting active lower-priority service.
- Add configurable probe interval.
- Add tests for fail down and fail back.
- Document strategy behaviour in `SOURCES.md` and `docs/ARCHITECTURE.md`.

## Acceptance Criteria
- `active_passive` uses backup only when primary is unhealthy.
- `priority_failover` fails back when a higher-priority endpoint becomes healthy.
- Dead endpoints do not block healthy endpoints.
- Tests simulate failures and recovery.

## Technical Notes
Relevant module: `upstream.py`.

## Priority
High

## Labels
upstream, operations, tests

---

# Issue: Add command-rate limiting and abuse controls for Telnet clients

## Summary
Protect the Telnet server from clients that send commands too quickly or repeatedly reconnect.

## Background
The server currently has max-client and output-queue bounds, but command input abuse is not strongly controlled.

## Proposed Work
- Track commands per session over a rolling window.
- Add config for max commands per minute.
- Disconnect or warn abusive clients.
- Add optional callsign validation strictness setting.
- Add tests for rate-limit behaviour.

## Acceptance Criteria
- Command rate limits are configurable.
- Excessive command clients are handled without affecting other clients.
- Tests cover allowed and blocked command rates.
- Behaviour is documented in `CONFIGURATION.md` and `COMMANDS.md`.

## Technical Notes
Relevant module: `telnet.py`.

## Priority
Medium

## Labels
telnet, security, operations

---

# Issue: Add structured JSON logging

## Summary
Introduce structured logging for application startup, upstream events, parser errors, dedupe decisions, client sessions, and admin mutations.

## Background
Production operations need searchable and parseable logs.

## Proposed Work
- Define logging fields and event names.
- Add config option for plain vs JSON logs.
- Log endpoint connect/disconnect/reconnect events.
- Log parse errors with endpoint and safe raw-line snippets.
- Log client connect/disconnect events.
- Ensure secrets are never logged.

## Acceptance Criteria
- Logs include source category and endpoint where relevant.
- Admin tokens are never logged.
- JSON mode emits valid JSON per line.
- Tests cover logger config where practical.

## Technical Notes
Relevant modules: `cli.py`, `app.py`, `upstream.py`, `telnet.py`, `admin.py`.

## Priority
Medium

## Labels
observability, operations, security

---

# Issue: Persist upstream status and operational metrics

## Summary
Persist endpoint status snapshots and basic counters so status survives process restarts and can be inspected historically.

## Background
Current endpoint metrics are in memory only.

## Proposed Work
- Add tables for endpoint status snapshots or current status.
- Persist reconnect counts, parse errors, last message time, and spots received.
- Add retention policy for historical snapshots if implemented.
- Extend admin `/status` to include persisted status where useful.

## Acceptance Criteria
- Endpoint status survives restart where meaningful.
- Metrics are updated without blocking hot paths.
- Tests cover persistence of endpoint status records.

## Technical Notes
Relevant modules: `upstream.py`, `storage.py`, `app.py`, `admin.py`.

## Priority
Medium

## Labels
storage, observability, operations

---

# Issue: Add Docker healthcheck and production Compose hardening

## Summary
Improve container runtime health and security settings.

## Background
The Dockerfile and Compose file are minimal.

## Proposed Work
- Add Dockerfile `HEALTHCHECK` using `deploy/healthcheck.sh` or an in-image equivalent.
- Consider read-only filesystem where feasible.
- Set resource hints/limits in example Compose comments if appropriate.
- Document persistent volume backup.
- Test on Docker host.

## Acceptance Criteria
- Docker health status reflects admin `/health`.
- Compose runtime remains functional.
- Deployment docs include backup and healthcheck notes.

## Technical Notes
Relevant files: `Dockerfile`, `docker-compose.yml`, `deploy/healthcheck.sh`, `docs/DEPLOYMENT.md`.

## Priority
Medium

## Labels
deployment, operations, security

---

# Issue: Test compatibility with common logging applications

## Summary
Validate Telnet workflow with common amateur radio logging software.

## Background
The main user-facing requirement is compatibility with classic DX Cluster/Telnet logging workflows.

## Proposed Work
- Identify target logging applications.
- Test login/callsign prompt.
- Test live spot display.
- Test filters if the application sends commands.
- Record compatibility notes.
- Adjust formatting/commands where practical.

## Acceptance Criteria
- At least two logging applications successfully connect and display spots.
- Known quirks are documented.
- Any required compatibility changes have tests.

## Technical Notes
Relevant modules: `telnet.py`, `formatting.py`, `COMMANDS.md`, `docs/USER_MANUAL.md`.

## Priority
Medium

## Labels
telnet, compatibility, docs

---

# Issue: Add optional PostgreSQL storage backend

## Summary
Add PostgreSQL support behind configuration while keeping SQLite as the default.

## Background
The project brief requested optional PostgreSQL support via configuration.

## Proposed Work
- Define a storage protocol/interface.
- Refactor SQLite-specific code behind the interface.
- Implement PostgreSQL backend with async or carefully managed sync access.
- Add config examples.
- Add tests using a service container or optional integration test marker.

## Acceptance Criteria
- SQLite remains default.
- PostgreSQL can store spots and filters.
- Backend selection is config-driven.
- Tests cover shared storage behaviour.

## Technical Notes
Relevant module: `storage.py`. Consider dependency impact carefully.

## Priority
Low

## Labels
storage, enhancement

---

# Issue: Add DXCC/country lookup enrichment

## Summary
Enrich spots with country/DXCC information when possible.

## Background
The canonical `Spot` model includes country fields, but they are not populated.

## Proposed Work
- Choose a maintainable callsign prefix/DXCC data source.
- Document source licensing and update process.
- Add enrichment helper.
- Add tests for known callsigns and edge cases.
- Add optional filters for country/DXCC include/exclude.

## Acceptance Criteria
- Country fields are populated for common prefixes.
- Unknown callsigns remain nullable.
- Data source licensing is documented.
- Tests cover enrichment and filters.

## Technical Notes
Relevant modules: `models.py`, `radio.py`, `filtering.py`.

## Priority
Low

## Labels
enhancement, filtering, docs

---

# Issue: Evaluate DXSummit connector feasibility

## Summary
Determine whether DXSummit can be integrated through a reliable and terms-compliant interface.

## Background
The project brief listed DXSummit as optional if reliable and scrape-safe. This requires research before implementation.

## Proposed Work
- Research available DXSummit interfaces and terms.
- Identify whether API access exists.
- Avoid brittle scraping unless explicitly allowed.
- Write a feasibility note in `SOURCES.md`.
- If feasible, create a separate implementation issue.

## Acceptance Criteria
- Feasibility is documented.
- Terms/compliance risk is stated.
- No connector is implemented unless access is acceptable.

## Technical Notes
Relevant file: `SOURCES.md`.

## Priority
Low

## Labels
connector, docs, research

---

# Issue: Evaluate PSK Reporter connector feasibility

## Summary
Determine whether PSK Reporter can be integrated in a technically feasible and compliant way.

## Background
PSK Reporter data volume and access rules may make direct live integration unsuitable.

## Proposed Work
- Research official access methods and terms.
- Identify rate limits and acceptable usage.
- Decide whether reports can be represented honestly as heard spots.
- Document findings.
- Create implementation issue only if feasible.

## Acceptance Criteria
- Feasibility and limitations are documented.
- No non-compliant scraping is added.
- Follow-up issue exists if implementation is appropriate.

## Technical Notes
Relevant file: `SOURCES.md`.

## Priority
Low

## Labels
connector, docs, research

---

# Issue: Evaluate WSPRnet connector feasibility

## Summary
Determine whether WSPRnet data can be represented cleanly and compliantly as heard spots.

## Background
WSPR reports are propagation reports, not classic human DX spots.

## Proposed Work
- Research access options and terms.
- Decide source marking and output format if implemented.
- Document risks and limitations.
- Create implementation issue only if feasible.

## Acceptance Criteria
- Feasibility is documented.
- Any future WSPR spots are clearly marked and not misrepresented.
- No implementation is done before feasibility is accepted.

## Technical Notes
Relevant files: `SOURCES.md`, `formatting.py`.

## Priority
Low

## Labels
connector, docs, research
