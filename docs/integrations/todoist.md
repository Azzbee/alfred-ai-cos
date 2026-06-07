# Todoist integration

Albert can create Todoist tasks on the user's behalf.

## Setup (one-time, per user)

1. **Todoist → Settings → Integrations → Developer → Copy your API
   token**.
2. In the Albert mobile app, **Settings → Integrations → Todoist**,
   paste the token, tap **Connect**.

## Backend wiring

- `app/services/todoist.py` — REST v2 client (`create_task`).
- `app/capabilities/providers/todoist_task.py` — risk level 2.
- Connection via `POST /api/v1/integrations/todoist/connect {access_token}`.

## Action payload

`target = {"content": str, "description": str | None, "due_string": str | None,
"priority": 1-4 | None, "project_id": str | None}`.

## What's deliberately not done

- Bidirectional sync (Todoist → Albert task ingestion). The capability
  is write-only for now; a follow-up worker would poll `GET /tasks` and
  upsert into Albert's `Task` table.
