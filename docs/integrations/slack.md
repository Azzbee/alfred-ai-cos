# Slack integration

Albert can post Slack messages on the user's behalf via the Web API.

## Setup (one-time, per workspace)

1. Visit https://api.slack.com/apps → **Create New App → From scratch**.
   Name "Albert", pick the workspace.
2. **OAuth & Permissions → Scopes → Bot Token Scopes**, add:
   - `chat:write`
   - `im:read` (only if you want DM ingestion later)
3. **Install to Workspace**. Copy the **Bot User OAuth Token** (starts
   with `xoxb-`).
4. In the Albert mobile app, **Settings → Integrations → Slack**, paste
   the bot token, tap **Connect**.

## Action payload

`target = {"channel": str, "text": str, "thread_ts": str | None}`.
`channel` may be a channel id (`C123…`), DM id (`D123…`), or user id
(`U123…`) for an IM.

## Backend wiring

- `app/services/slack.py` — Web API client (`post_message`,
  `conversations_list` for the future DM ingestion).
- `app/capabilities/providers/slack_message.py` — risk level 3.

## What's deliberately not done

- OAuth-flow installation. The bot-token paste path is enough for a
  single workspace.
- Reading DMs / threads. The `conversations_list` helper exists; a
  follow-up worker would walk DMs and ingest them into `Message` so
  the priority engine ranks Slack pings alongside email.
