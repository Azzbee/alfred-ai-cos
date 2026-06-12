# Mobile dev scripts

## Standalone iOS install — the durable phone-on-your-desk flow

The recommended dev loop for testing changes on a real iPhone. Albert appears
on the home screen, takes JS updates over the air, doesn't need Expo Go or
Metro running on your laptop.

| Script   | Command                  | What it does                                                                                              |
| -------- | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| Register | `bun run device:ios`     | Add this iPhone's UDID to your Apple Dev account + install the provisioning profile. One-time per device. |
| Build    | `bun run build:ios`      | Kick off an EAS cloud build (preview profile, internal distribution, ~15 min).                            |
| Install  | `bun run install:ios`    | Print the install link + QR for the latest finished build.                                                |
| Update   | `bun run update:preview` | Ship JS changes over the air (instant). Skips the rebuild.                                                |

The full setup is in `mobile/EAS.md`. The scripts wrap `eas-cli` with timeout
handling, env-file loading, and clear next-step printing so the flow is one
command per step instead of three flags and a memorized incantation.

`bun run login` is the equivalent of `bunx eas login` but uses the workspace's
local `eas-cli` so the version always matches `eas.json`'s `cli.version`.

## Web dev proxy — `start:web` + `proxy`

Expo can run as a web app (`expo start --web`). The browser blocks cross-
origin requests from `http://localhost:8081` to `https://albert.alfredassistants.com`,
which kills login and every API call.

`dev-api-proxy.mjs` is a 95-line HTTP server on `:8000` that:

- Adds CORS headers for the local Expo origins,
- Handles the browser's OPTIONS preflight,
- Forwards `/api/v1/*` to production over HTTPS.

`mobile/src/api/client.ts` is hard-coded to point at `localhost:8000` when
`Platform.OS === "web" && __DEV__`, so the proxy is the only thing needed for
web dev. `bun run start:web` boots both together.

The proxy never touches anything outside `/api/v1/*` and never persists state.
It is dev-only — production web hosting (if we ever do it) would use a real
reverse proxy on the same origin.

## What's NOT here

The earlier PR also shipped:

- An Expo Go + ngrok tunnel flow (`start-phone.sh`) — superseded by the
  standalone EAS build, deliberately not ported.
- A `postinstall` patcher for `@expo/cli` that mutates `node_modules` to
  work around a Node 24 spawn bug — preferred fix is to pin Node 22 or wait
  for upstream. Not ported.
- A `stop` script that calls `pkill cloudflared` — destructive on the VPS
  (kills the prod tunnel). Not ported.
