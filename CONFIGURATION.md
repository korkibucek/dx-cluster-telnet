# Configuration

Configuration is loaded from YAML.

| Field | Required | Default | Description |
|---|---:|---|---|
| `server.listen_host` | No | `0.0.0.0` | Telnet bind address. |
| `server.listen_port` | No | `7373` | Telnet port for logging clients. |
| `server.max_clients` | No | `100` | Maximum concurrent Telnet clients. |
| `database.url` | No | `sqlite:///data/rbn-dxcluster.sqlite3` | SQLite database URL. |
| `upstreams.<category>.enabled` | No | `true` | Enables a whole source category. |
| `upstreams.<category>.strategy` | No | `active_active` | Feed strategy. |
| `upstreams.<category>.max_feeds` | No | `10` | Maximum endpoints used for the category. |
| `upstreams.<category>.endpoints[]` | Yes | none | Endpoint list with `name`, `host`, and `port`. |
| `dedupe.window_seconds` | No | `60` | Duplicate matching window. |
| `dedupe.frequency_tolerance_khz` | No | `0.5` | Frequency bucket tolerance. |
| `admin.listen_host` | No | `127.0.0.1` | Admin HTTP bind address. Keep localhost unless protected. |
| `admin.auth_token` | No | `null` | Required for mutating admin actions when set; leave unset to disable mutation. |

Supported source categories include `rbn_cw_rtty`, `rbn_ft8`, `classic_cluster`, `dxsummit`, `pskreporter`, `wsprnet`, and future categories matching the internal enum.

Each endpoint tracks health independently and can be disabled without disabling the category.
