#!/usr/bin/env bash
set -euo pipefail
docker compose pull || true
docker compose up --build -d
