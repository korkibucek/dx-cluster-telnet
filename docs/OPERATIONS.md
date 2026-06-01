# Operations

## Health

- Telnet: connect to TCP `7373` and enter a callsign.
- Admin health: `curl http://127.0.0.1:8080/health`.
- Source status: `curl http://127.0.0.1:8080/sources` or Telnet `show/sources`.

## Metrics

The in-process status includes counters for received spots, deduplicated spots, client sends, reconnects, parse errors, and endpoint message rates.

## Backup

Back up the SQLite database file configured by `database.url` and the YAML config.


## Feed control

Set `admin.auth_token` before using mutating admin actions. Examples:

```bash
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/disable-feed?endpoint=rbn-main'
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/enable-feed?endpoint=rbn-main'
curl -X POST -H 'X-Admin-Token: change-me' 'http://127.0.0.1:8080/admin/reconnect-feed?endpoint=rbn-main'
```
