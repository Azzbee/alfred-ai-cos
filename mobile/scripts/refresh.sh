#!/usr/bin/env bash
# Full reset + start Expo for phone testing.
# Run from anywhere:  bash mobile/scripts/refresh.sh
# Or from mobile/:   bash scripts/refresh.sh
#
# Why this script exists:
#   - "bun run start" can hang silently when spawning the expo CLI wrapper
#   - Zombie Metro processes from earlier runs block port 8081
#   - Starting via `node …/expo/bin/cli` is reliable (~2s to QR code)

set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$MOBILE_DIR/.." && pwd)"
EXPO_CLI="$REPO_ROOT/node_modules/expo/bin/cli"

echo "── 1/4  Stopping old Expo/Metro on ports 8081–8083"
for port in 8081 8082 8083; do
  lsof -tiTCP:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
done
pkill -f "expo start" 2>/dev/null || true
pkill -f "expo/bin/cli" 2>/dev/null || true
sleep 1

echo "── 2/4  Clearing Metro cache"
rm -rf "$MOBILE_DIR/.expo" "$MOBILE_DIR/node_modules/.cache" 2>/dev/null || true

echo "── 3/4  Checking port 8081 is free"
if lsof -iTCP:8081 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "ERROR: port 8081 still in use. Run: lsof -iTCP:8081"
  exit 1
fi
echo "       Port 8081 is free ✓"

echo "── 4/4  Starting Expo for phone"
echo ""
echo "  For a standalone Albert app (home screen + OTA updates), NOT Expo Go:"
echo "    bun run device:ios && bun run build:ios && bun run install:ios"
echo ""
echo "  For Expo Go preview (requires Mac + tunnel):"
echo "    bun run start:phone"
echo ""
exec bash "$MOBILE_DIR/scripts/start-phone.sh"
