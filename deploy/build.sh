#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROXY_HOST="${BUILD_PROXY_HOST:-$(ip route show default | awk 'NR==1 {print $3}')}"
PROXY_PORT="${BUILD_PROXY_PORT:-7890}"
exec "$DEPLOY_DIR/compose.sh" build --build-arg "MAVEN_PROXY_HOST=$PROXY_HOST" --build-arg "MAVEN_PROXY_PORT=$PROXY_PORT" --build-arg "HTTP_PROXY=http://$PROXY_HOST:$PROXY_PORT" --build-arg "HTTPS_PROXY=http://$PROXY_HOST:$PROXY_PORT" api
