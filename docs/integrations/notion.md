# Notion integration

Albert creates pages in a Notion database the user has shared with an
internal integration.

## What it can do

- Create a page in a chosen Notion database from a commitment, draft, or
  share-sheet capture. The created page id and url come back so the
  mobile app can deep-link the user to it.

## Setup (one-time, per user)

1. Open Notion, go to **Settings → Connections → Develop or manage
   integrations → New integration**. Name it "Albert", workspace = the
   user's. Capabilities: at least **Insert content**.
2. Copy the **Internal Integration Secret** (starts with `ntn_…`).
3. Open the database where Albert should create pages. Click **`…` →
   Connections → Add connection → Albert**.
4. Get the database id from the URL:
   `https://www.notion.so/<workspace>/<32-char-id>?v=…` — the 32-char id
   (with no dashes) is the `database_id`. The Albert API accepts both
   the dashed and undashed form.
5. In the Albert mobile app, **Settings → Integrations → Notion**, paste
   the integration secret + database id, tap **Connect**. Backend stores
   them encrypted (Fernet) on `ConnectedAccount(provider=notion)`.

## What's required of the database

A title column called `Name` (this is the Notion default). Any other
columns are optional; Albert can populate them when the proposal carries
a `properties` payload that matches the database schema.

## Backend wiring

- `app/services/notion.py` — REST client (`create_page`, `whoami`).
- `app/capabilities/providers/notion_page.py` — capability provider,
  risk level 2 (reversible write). Always registered; gated per-user by
  the presence of `ConnectedAccount(provider=notion)`.
- `app/api/v1/integrations.py` — connect / disconnect / list endpoints.

## Failure modes

- **No Notion connection on the user** → `CapabilityError("No Notion
  account connected. Connect Notion in Settings.")`.
- **Bad token** → Notion returns 401; surfaced as `CapabilityError(
  "Notion create_page failed: HTTP 401 …")`.
- **Database missing the integration permission** → Notion returns 404
  with a clear message.

## What's deliberately not done

- OAuth (public integration) flow. The internal-integration paste-token
  path is simpler and sufficient for a single-user beta; the public
  OAuth flow is a follow-up when we want a frictionless install.
- Reading from Notion (search pages, query database). The capability is
  write-only for now.
