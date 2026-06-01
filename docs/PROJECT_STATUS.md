# Project Status

## Status summary

`rbn-dxcluster` is at an **initial functional scaffold** stage. The core modules exist and the unit tests pass, but the system still needs integration testing, production hardening, compatibility testing with real amateur radio logging programs, and GitHub Issue import.

## Current milestone

Initial scaffold completed:

- Source package created.
- CLI entrypoint created.
- YAML config loader created.
- Telnet server created.
- Upstream endpoint/supervisor architecture created.
- Deduplication created.
- SQLite persistence created.
- Local admin API created.
- Docker/Compose files created.
- CI workflow created.
- Basic documentation created.
- Manual backlog created.

## Project-management gap

The original project instructions requested real GitHub Issues. They were not created because this local checkout had no GitHub remote and no GitHub CLI. `BACKLOG_TO_IMPORT.md` must be imported manually once the project is connected to GitHub.

## Production-readiness assessment

| Area | Current status | Production readiness |
|---|---|---|
| Python packaging | Implemented | Medium |
| Config loading | Implemented, minimal validation | Medium-low |
| Telnet server | Implemented line-oriented server | Medium-low |
| Telnet protocol compatibility | Basic commands only | Low |
| RBN/classic parsing | Basic parser | Medium-low |
| Redundant endpoints | Implemented foundation | Medium |
| Active-active strategy | Implemented | Medium |
| Active-passive/priority failover | Basic foundation | Low-medium |
| Dedupe | Implemented simple algorithm | Medium |
| SQLite persistence | Basic tables | Medium-low |
| Saved filters | Implemented | Medium |
| Admin status | Implemented | Medium |
| Admin mutations | Implemented with token | Medium-low |
| Admin audit logs | Not implemented | Low |
| Tests | Unit-focused | Medium-low |
| Integration tests | Minimal/not complete | Low |
| Docker runtime | Files present | Needs live daemon test |
| CI | Basic workflow present | Medium |
| Security | Basic defaults | Medium-low |
| Observability | Basic counters/logging | Low-medium |
| Documentation | Expanded handover docs | Medium |

## Known blockers / environment limitations

- No GitHub remote was configured in the working environment.
- No GitHub Issues could be created from the environment.
- Docker runtime validation depends on a host with a running Docker daemon.
- Live upstream testing depends on network access and responsible handling of high-volume feeds.

## Recommended acceptance gates before claiming production-ready

1. GitHub Issues imported and triaged.
2. Docker image builds on CI or a developer host.
3. Docker Compose runtime smoke test passes.
4. Fake upstream integration tests pass.
5. Real RBN CW/RTTY smoke test passes.
6. Real RBN FT8 high-volume test is profiled with conservative limits.
7. At least one classic cluster endpoint is tested.
8. At least one real logging application successfully connects and receives filtered spots.
9. Admin token mutation test is performed locally.
10. Security review confirms admin API is not exposed publicly.

## Handover priorities

### Priority 1: Project management

Import `BACKLOG_TO_IMPORT.md` into GitHub Issues. This is the most important non-code task because future work should be issue-driven.

### Priority 2: Integration tests

Add fake upstream TCP server tests to prove reconnect, active-active ingestion, duplicate merge, and Telnet fanout together.

### Priority 3: Parser hardening

Capture real upstream samples and add regression tests. This will quickly reveal line-format assumptions.

### Priority 4: Operational hardening

Add audit logs, migrations, better status persistence, Docker healthchecks, and deployment validation.

### Priority 5: Compatibility testing

Test against actual logging clients and refine command output/format compatibility.
