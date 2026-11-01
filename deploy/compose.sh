#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec docker compose --env-file "$DEPLOY_DIR/.env" -p restaurant-practice -f "$DEPLOY_DIR/../../restaurant-reservation-sut/docker-compose.yml" -f "$DEPLOY_DIR/compose.test.yml" "$@"
