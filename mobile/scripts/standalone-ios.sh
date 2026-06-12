#!/usr/bin/env bash
# Standalone Albert app on your iPhone (NOT Expo Go).
#
# Flow:
#   1. bun run device:ios     — register your phone (Settings profile QR)
#   2. bun run build:ios      — cloud build (~15 min, needs Apple Developer)
#   3. bun run install:ios    — print install link + QR from latest build
#   4. bun run update:preview — push JS changes to the installed app
#
# start:phone / Expo Go is a different workflow and will NOT install Albert
# on your home screen or receive eas update bundles.

set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$MOBILE_DIR/.." && pwd)"
NODE_BIN="${NODE_BIN:-$(command -v node)}"
EAS_RUN="$REPO_ROOT/node_modules/eas-cli/bin/run"
EAS=""
if [ -x "$EAS_RUN" ]; then
  EAS="$NODE_BIN"
  EAS_ARGS=("$EAS_RUN")
else
  for candidate in \
    "$REPO_ROOT/node_modules/.bin/eas" \
    "$MOBILE_DIR/node_modules/.bin/eas" \
    "$(command -v eas 2>/dev/null || true)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      EAS="$candidate"
      break
    fi
  done
  EAS_ARGS=()
fi
if [ -z "$EAS" ]; then
  EAS="bunx"
  EAS_ARGS=(eas)
fi

run_eas() {
  if [ "${#EAS_ARGS[@]}" -gt 0 ]; then
    "$EAS" "${EAS_ARGS[@]}" "$@"
  else
    "$EAS" "$@"
  fi
}

# EAS can hang waiting for browser login; fail fast with a clear message.
run_eas_timed() {
  local secs="$1"
  shift
  local tmp pid i rc
  tmp="$(mktemp)"
  if [ "${#EAS_ARGS[@]}" -gt 0 ]; then
    "$EAS" "${EAS_ARGS[@]}" "$@" >"$tmp" 2>&1 &
  else
    "$EAS" "$@" >"$tmp" 2>&1 &
  fi
  pid=$!
  i=0
  while kill -0 "$pid" 2>/dev/null && [ "$i" -lt "$secs" ]; do
    sleep 1
    i=$((i + 1))
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    cat "$tmp"
    rm -f "$tmp"
    return 124
  fi
  wait "$pid"
  rc=$?
  cat "$tmp"
  rm -f "$tmp"
  return $rc
}

CURL_BIN="$(command -v curl 2>/dev/null || echo /usr/bin/curl)"

print_qr() {
  local url="$1"
  if "$NODE_BIN" -e "require('qrcode-terminal').generate(process.argv[1])" "$url" 2>/dev/null; then
    echo ""
  else
    echo "  (Could not render QR — open the URL below on your phone instead)"
    echo ""
  fi
}

cd "$MOBILE_DIR"

# Load mobile/.env.local (EXPO_TOKEN, etc.) for EAS commands.
ENV_FILE="$MOBILE_DIR/.env.local"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

echo "════════════════════════════════════════════════════════════"
echo "  Albert — standalone iPhone install (not Expo Go)"
echo "════════════════════════════════════════════════════════════"
echo ""

get_eas_account() {
  run_eas whoami 2>/dev/null | head -1 | tr -d '\r\n'
}

if ! ACCOUNT="$(get_eas_account)" || [ -z "$ACCOUNT" ]; then
  echo "ERROR: Not logged in to Expo."
  echo "  Run:  cd mobile && bun run login"
  echo "  Or add EXPO_TOKEN to mobile/.env.local (expo.dev/settings/access-tokens)"
  exit 1
fi

echo "  Expo account: $ACCOUNT"

SLUG="albert"
OWNER="$(node -e "console.log(require('./app.json').expo.owner || '')" 2>/dev/null || true)"
if [ -z "$OWNER" ]; then
  OWNER="$ACCOUNT"
fi

if [ "$OWNER" != "$ACCOUNT" ]; then
  echo ""
  echo "  NOTE: app.json owner is \"${OWNER}\" but you are logged in as \"${ACCOUNT}\"."
  echo "  You must be a member of the ${OWNER} org on expo.dev, or builds will fail."
  echo "  Ask the org owner to invite you, or run: bunx eas init (under your account)."
fi

MODE="${1:-install}"

case "$MODE" in
  device)
    echo ""
    echo "── Register this iPhone for internal installs"
    echo ""
    echo "  EAS will ask a few questions in THIS terminal — answer them here:"
    echo "    1. \"Use the ${OWNER} account?\"  →  Yes"
    echo "    2. Sign in with your Apple Developer Apple ID (\$99/yr)"
    echo "    3. EAS prints a link/QR — scan on your phone in Safari"
    echo "    4. Install the profile: Settings → General → VPN & Device Management"
    echo "    5. Then run:  bun run build:ios"
    echo ""
    echo "  (If nothing happens for 30s, press Enter once — it may be waiting for input.)"
    echo ""
    if [ "${#EAS_ARGS[@]}" -gt 0 ]; then
      exec "$EAS" "${EAS_ARGS[@]}" device:create
    else
      exec "$EAS" device:create
    fi
    ;;

  build)
    echo ""
    echo "── Starting iOS preview build on EAS (standalone app + OTA updates)"
    echo ""
    echo "  Requires: Apple Developer account (\$99/yr) linked in EAS."
    echo "  Your phone must already be registered (bun run device:ios)."
    echo ""
    run_eas build --profile preview --platform ios
    exit $?
    ;;

  update)
    MSG="${2:-mobile update $(date +%Y-%m-%d)}"
    echo ""
    echo "── Publishing JS update to preview channel"
    echo ""
    run_eas update --branch preview -m "$MSG"
    exit $?
    ;;

  install|*)
    echo ""
    echo "── Latest finished iOS preview build"
    echo ""

    BUILD_JSON="$(
      run_eas build:list \
        --platform ios \
        --profile preview \
        --status finished \
        --limit 1 \
        --json \
        --non-interactive 2>/dev/null || true
    )"

    BUILD_ID=""
    BUILD_URL=""
    if [ -n "$BUILD_JSON" ]; then
      read -r BUILD_ID BUILD_URL <<EOF
$(printf '%s' "$BUILD_JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    builds = data if isinstance(data, list) else data.get('builds', data)
    if not builds:
        sys.exit(0)
    b = builds[0]
    bid = b.get('id', '')
    url = b.get('artifacts', {}).get('buildUrl') or b.get('buildUrl') or ''
    print(bid)
    print(url)
except Exception:
    pass
" 2>/dev/null)
EOF
    fi

    if [ -z "$BUILD_ID" ]; then
      echo "  No finished iOS preview build found yet."
      echo ""
      echo "  Do this once:"
      echo "    1. bun run device:ios    # register phone + install profile"
      echo "    2. bun run build:ios     # cloud build (~15 min)"
      echo "    3. bun run install:ios   # this script — install QR"
      echo ""
      echo "  start:phone is Expo Go only — it cannot install Albert on your home screen."
      exit 1
    fi

    INSTALL_PAGE="https://expo.dev/accounts/${OWNER}/projects/${SLUG}/builds/${BUILD_ID}"

    echo "  Build page (open on phone → Install → scan QR):"
    echo "    $INSTALL_PAGE"
    echo ""
    echo "  On iPhone:"
    echo "    1. Open the link above in Safari"
    echo "    2. Tap Install under Build artifact"
    echo "    3. Install provisioning profile if prompted (Settings)"
    echo "    4. Albert appears on your home screen"
    echo ""
    echo "  Install QR (opens build page — tap Install there):"
    echo ""
    print_qr "$INSTALL_PAGE"

    if [ -n "$BUILD_URL" ]; then
      echo "  Direct .ipa (advanced): $BUILD_URL"
      echo ""
    fi

    echo "  After you change JS/screens, push an OTA update:"
    echo "    bun run update:preview"
    echo ""
    echo "  Force-quit Albert and reopen to fetch the update."
    echo "════════════════════════════════════════════════════════════"
    ;;
esac
