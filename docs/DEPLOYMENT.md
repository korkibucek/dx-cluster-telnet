# Deployment

## Docker Compose

```bash
docker compose up --build -d
```

Expose TCP `7373` to trusted client networks. Keep the admin API bound to `127.0.0.1` or place it behind authentication before remote exposure.

## Host deployment

Use the CLI entrypoint:

```bash
rbn-dxcluster serve --config /etc/rbn-dxcluster/config.yaml
```

For production, run it under systemd or a container restart policy and persist the SQLite `data/` directory.
