# Installation

## Requirements

- Python 3.12+
- Network access from the server to configured Telnet feeds
- Docker and Docker Compose for container deployment

## Local install

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
rbn-dxcluster serve --config config/config.example.yaml
```

## Docker install

```bash
docker compose up --build -d
```

## Logger setup

Point your logging application at the host running `rbn-dxcluster`, TCP port `7373`, using the normal Telnet DX Cluster connection profile. Enter your callsign when prompted.
