#!/usr/bin/env bash
# Start Metro + ngrok tunnel for **Expo Go only** on your phone.
#
# For a real Albert icon on your home screen + OTA updates (NOT Expo Go):
#   bun run device:ios    → register phone + provisioning profile
#   bun run build:ios     → EAS cloud build
#   bun run install:ios   → install QR / link
#   bun run update:preview → push JS updates to the installed app
#
# Uses system ngrok directly (NOT "expo start --tunnel", which hangs with
# the bundled @expo/ngrok binary on this machine).
#
# Setup:  add NGROK_AUTHTOKEN to mobile/.env.local (see .env.local.example)
# Run:    bun run start:phone

set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$MOBILE_DIR/.." && pwd)"
EXPO_CLI="$REPO_ROOT/node_modules/expo/bin/cli"
NODE_BIN="${NODE_BIN:-$(command -v node)}"
METRO_PORT=8081
METRO_ADDR="127.0.0.1:${METRO_PORT}"
ENV_FILE="$MOBILE_DIR/.env.local"
NGROK_API="http://127.0.0.1:4040"

METRO_PID=""
NGROK_PID=""

cleanup() {
  echo ""
  echo "Stopping Metro + ngrok..."
  [ -n "$METRO_PID" ] && kill "$METRO_PID" 2>/dev/null || true
  [ -n "$NGROK_PID" ] && kill "$NGROK_PID" 2>/dev/null || true
  lsof -tiTCP:"$METRO_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
  pkill -f "ngrok http" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

CURL_BIN="$(command -v curl 2>/dev/null || echo /usr/bin/curl)"

wait_for_metro() {
  for _ in $(seq 1 45); do
    "$CURL_BIN" -sf --max-time 2 "http://${METRO_ADDR}/status" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

get_ngrok_url() {
  "$CURL_BIN" -sf --max-time 2 "$NGROK_API/api/tunnels" 2>/dev/null \
    | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for t in data.get('tunnels', []):
        u = t.get('public_url', '')
        if u.startswith('https://'):
            print(u)
            break
except Exception:
    pass
" 2>/dev/null || true
}

verify_tunnel_manifest() {
  local host="$1"
  local tmp http_code body
  tmp="$(mktemp)"
  http_code="$("$CURL_BIN" -sS --max-time 20 \
    -H "Accept: application/expo+json" \
    -H "expo-platform: ios" \
    -H "ngrok-skip-browser-warning: 1" \
    -o "$tmp" -w "%{http_code}" \
    "https://${host}/" 2>/dev/null || echo "000")"
  body="$(cat "$tmp")"
  rm -f "$tmp"

  if [ "$http_code" != "200" ]; then
    echo "ERROR: tunnel manifest HTTP ${http_code} (expected 200)" >&2
    echo "$body" | head -c 200 >&2
    echo >&2
    return 1
  fi

  printf '%s' "$body" | python3 -c "
import sys, json
raw = sys.stdin.read()
if raw.lstrip().startswith('<'):
    print('ERROR: ngrok returned HTML, not Expo manifest', file=sys.stderr)
    sys.exit(1)
data = json.loads(raw)
host_uri = data.get('extra', {}).get('expoClient', {}).get('hostUri', '')
if '${host}' not in host_uri:
    print(f'ERROR: manifest hostUri={host_uri!r}', file=sys.stderr)
    sys.exit(1)
print(host_uri)
"
}

# ── Load token ───────────────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

NGROK_AUTHTOKEN="$(printf '%s' "${NGROK_AUTHTOKEN:-}" | tr -d ' \t\r\n\"' )"

if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your_token_from_ngrok.com/dashboard" ]; then
  echo "ERROR: No NGROK_AUTHTOKEN in mobile/.env.local"
  echo "  Open mobile/.env.local and set:"
  echo "    NGROK_AUTHTOKEN=<paste from https://dashboard.ngrok.com/get-started/your-authtoken>"
  echo ""
  echo "  Do NOT copy .env.local.example over .env.local — that wipes your token."
  exit 1
fi

NGROK_BIN=""
for candidate in /opt/homebrew/bin/ngrok /usr/local/bin/ngrok; do
  if [ -x "$candidate" ]; then
    NGROK_BIN="$candidate"
    break
  fi
done
if [ -z "$NGROK_BIN" ]; then
  NGROK_BIN="$(command -v ngrok 2>/dev/null || true)"
fi
if [ -z "$NGROK_BIN" ] || [ ! -x "$NGROK_BIN" ]; then
  echo "ERROR: ngrok not installed.  Run:  brew install ngrok"
  exit 1
fi
export NGROK_AUTHTOKEN

# Node 24 hangs spawning expo-updates/bin/cli.js via shebang — patch before Metro.
"$NODE_BIN" "$MOBILE_DIR/scripts/patch-expo-updates-spawn.mjs"

# ── 1. Clean up ──────────────────────────────────────────────────────────────
echo "── 1/4  Cleaning up (ngrok: $NGROK_BIN)"
for port in 8081 8082 4040; do
  lsof -tiTCP:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
done
pkill -f "expo/bin/cli" 2>/dev/null || true
pkill -f "ngrok http" 2>/dev/null || true
sleep 1
echo "       done ✓"

# ── 2. Start ngrok (before Metro — avoids restart race / ERR_NGROK_3004) ────
echo "── 2/4  Starting ngrok tunnel"
# Explicit http://127.0.0.1 — Metro is plain HTTP on IPv4 (not https, not ::1).
NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN" \
  "$NGROK_BIN" http "http://${METRO_ADDR}" --host-header="localhost:${METRO_PORT}" \
  --log=stdout > /tmp/albert-ngrok.log 2>&1 &
NGROK_PID=$!

TUNNEL_URL=""
for _ in $(seq 1 30); do
  TUNNEL_URL="$(get_ngrok_url)"
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  if ! kill -0 "$NGROK_PID" 2>/dev/null; then
    echo "ERROR: ngrok exited:"
    cat /tmp/albert-ngrok.log
    exit 1
  fi
  printf "."
  sleep 1
done
echo ""

if [ -z "$TUNNEL_URL" ]; then
  echo "ERROR: ngrok tunnel URL not found. Log:"
  cat /tmp/albert-ngrok.log
  exit 1
fi

TUNNEL_HOST="${TUNNEL_URL#https://}"
echo "       $TUNNEL_URL ✓"

# ── 3. Start Metro once with tunnel in manifest ─────────────────────────────
echo "── 3/4  Starting Metro (tunnel-aware manifest)"
cd "$MOBILE_DIR"
unset REACT_NATIVE_PACKAGER_HOSTNAME
# Expo Go + manual ngrok: proxy URL must be http://host:80, QR must be exp://host:80
# https://github.com/expo/expo/issues/43335#issuecomment-2661820152
EXPO_PACKAGER_PROXY_URL="http://${TUNNEL_HOST}:80" \
EXPO_NO_TELEMETRY=1 \
"$NODE_BIN" "$EXPO_CLI" start --port "$METRO_PORT" --lan > /tmp/albert-metro.log 2>&1 &
METRO_PID=$!

if ! wait_for_metro; then
  echo "ERROR: Metro did not start."
  exit 1
fi
echo "       Metro ready ✓"

# ── 4. Verify phone can load manifest through tunnel ────────────────────────
echo "── 4/4  Verifying tunnel → Metro"
MANIFEST_HOST=""
VERIFY_ERR=""
for _ in $(seq 1 10); do
  if VERIFY_OUT="$(verify_tunnel_manifest "$TUNNEL_HOST" 2>&1)"; then
    MANIFEST_HOST="$VERIFY_OUT"
    break
  fi
  VERIFY_ERR="$VERIFY_OUT"
  printf "."
  sleep 2
done
echo ""

if [ -z "$MANIFEST_HOST" ]; then
  echo "WARN:  Could not verify tunnel manifest (Metro may still work)."
  echo "  ${VERIFY_ERR:-unknown error}"
  echo "  Still try the QR below — URL must end with :80"
  echo ""
else
  echo "       manifest hostUri: $MANIFEST_HOST ✓"
fi

EXP_URL="exp://${TUNNEL_HOST}:80"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  READY — connect your phone:"
echo ""
echo "  Scan the QR below. URL MUST include :80 at the end:"
echo "    ${EXP_URL}"
echo ""
echo "  iOS:     Camera app → tap banner → Expo Go"
echo "  Android: Expo Go → Scan QR code"
echo ""
echo "  If you see ERR_NGROK_3004, you scanned the wrong QR"
echo "  (Expo prints exp://${TUNNEL_HOST} without :80 — ignore that)."
echo ""
echo "  QR code:"
echo ""

# npx qrcode-terminal hangs when stdin is not a TTY (always true inside shell scripts).
if "$NODE_BIN" -e "require('qrcode-terminal').generate(process.argv[1])" "$EXP_URL" 2>/dev/null; then
  echo ""
else
  echo "  (QR render failed — copy the URL above into Notes and tap it)"
  echo ""
fi

echo "  Metro logs: tail -f /tmp/albert-metro.log"
echo "  Ctrl+C stops Metro + ngrok."
echo "════════════════════════════════════════════════════════════"
echo ""

wait "$METRO_PID"
