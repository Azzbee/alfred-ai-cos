# Share to Albert from the iOS Share Sheet

Send any URL or text from another iOS app into Albert as a Task.

## How it works

iOS Shortcut: receives `URL` or `Text` from the share sheet → POSTs to
`https://albert.alfredassistants.com/api/v1/share` with the user's
session token in the Authorization header → backend creates a Task.

This uses a Shortcut (one minute to set up) rather than a native Share
Extension target because the latter requires breaking out of the Expo
managed workflow.

## Setup (one-time, ~3 minutes)

### 1. Grab your session token

1. Open Albert → **Settings → Developer → Show session token**.
   (Backend already returns this on `/api/v1/me`; the mobile UI
   exposes it via a copy button.)
2. Tap **Copy**.

### 2. Build the Shortcut

1. Open the **Shortcuts** app on iOS.
2. Tap **+** to create a new Shortcut.
3. Tap the **i** at the bottom → **Show in Share Sheet** = ON.
   Accept types = URLs + Text.
4. Add **Get Contents of URL** action.
   - URL: `https://albert.alfredassistants.com/api/v1/share`
   - Method: **POST**
   - Headers:
     - `Authorization: Bearer <PASTE_YOUR_TOKEN>`
     - `Content-Type: application/json`
   - Request Body: **JSON**, with these fields:
     - `url`: Shortcut Input (drag from the magic-variables picker)
     - `text`: leave empty, OR set to Shortcut Input if accepting text
5. Add **Show Notification** action.
   - Title: `Saved to Albert`
   - Body: drag the response's `title` field.
6. Name the Shortcut **Send to Albert**.

### 3. Use it

Any app → Share Sheet → **Send to Albert**. A notification confirms
the task was created.

## Backend wiring

- `app/api/v1/share.py` — accepts `{"url": str | None, "text": str |
  None, "title": str | None}`. Either url or text required.
- Resolves a title: explicit `title` wins, else first line of `text`,
  else URL host, else "Shared item".
- Stores both url + text in `description` (capped at 4KB).
- Returns `{"task_id", "title"}`.

## Failure modes

- **Token expired**: 401. Re-copy from Settings.
- **No body**: 400. The Shortcut must POST at least one of url/text.

## What's deliberately not done

- Native iOS Share Extension target. The Shortcut path delivers 90% of
  the UX with zero blast radius. A Share Extension would require
  ejecting from managed Expo, which we don't want yet.
