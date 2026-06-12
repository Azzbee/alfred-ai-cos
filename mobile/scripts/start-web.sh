#!/usr/bin/env bash
# Start the CORS dev proxy + Expo web together.
# The proxy forwards localhost:8000/api/v1 → production so browser dev login works.

set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$MOBILE_DIR/.." && pwd)"
EXPO_CLI="$REPO_ROOT/node_modules/expo/bin/cli"

# Free ports before starting.
for port in 8081 8000; do
  lsof -tiTCP:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
done

echo "── Starting API dev proxy on :8000"
node "$MOBILE_DIR/scripts/dev-api-proxy.mjs" &
PROXY_PID=$!

cleanup() {
  kill "$PROXY_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 0.5
echo "── Starting Expo web on :8081"
echo "   Open http://localhost:8081 in your browser."
echo ""

cd "$MOBILE_DIR"
node "$MOBILE_DIR/scripts/patch-expo-updates-spawn.mjs"
EXPO_NO_TELEMETRY=1 node "$EXPO_CLI" start --web --port 8081
