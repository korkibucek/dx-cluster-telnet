# Security

- Telnet access is unauthenticated by default for DX Cluster compatibility.
- Limit exposure with firewall rules when running on public hosts.
- Admin HTTP binds to `127.0.0.1` by default; mutating actions require `admin.auth_token`, and remote exposure should still be protected by an authenticated reverse proxy.
- Do not put upstream credentials in config unless future connectors require them; secrets must not be logged.
- Per-client queue limits and max-client settings reduce abuse risk.
