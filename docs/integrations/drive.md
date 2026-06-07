# Google Drive context

Read-only Drive access so the meeting-prep and draft surfaces can pull
the latest doc on a project.

## Scope addition

The Drive scopes were added to `settings.google_scopes` in commit
*P10*. Adding scopes invalidates every user's existing Google OAuth
token — the next sign-in surfaces a fresh consent screen including
"See and download all your Drive files."

## Endpoints

- `GET /api/v1/drive/search?q=...&limit=10` — file metadata only.
- `GET /api/v1/drive/files/{file_id}/text` — plain-text content,
  capped at 100KB (returned `truncated=true` when clipped).

## Behaviour

- Google Docs → exported as `text/plain`.
- Sheets → exported as `text/csv`.
- Plain-text / Markdown / JSON / CSV → raw bytes decoded as UTF-8.
- Binary types → returns a stub string and the webViewLink for download.

## What's deliberately not done

- Per-file ACL respect beyond Drive's own permission model. We pass the
  user's OAuth token to Drive; Drive enforces.
- Active context retrieval baked into draft generation. The endpoint
  exists; the Memory Agent would wire it later.
