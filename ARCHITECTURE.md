# Architecture

This documents the shape of Albert's first slice and the decisions behind it. It maps
to the PRD (`albert_ai_assistant_prd.md`) so the two stay aligned.

## Goal of the slice

Prove one thing (PRD section 28): Albert can look at your inbox and tell you what you
are forgetting. Everything here serves the path:

```
Gmail OAuth → ingestion → classification + commitment extraction → priority → Today → draft → approve
```

## System shape

```
┌─────────────┐      HTTPS (JWT)      ┌──────────────────────────────────────┐
│  Expo app   │ ───────────────────► │  FastAPI (app.main)                    │
│  Today/     │ ◄─────────────────── │   api/v1: auth, sync, today,           │
│  Connect    │   albert:// deeplink │           commitments, drafts, actions │
└─────────────┘                      └───────────────┬────────────────────────┘
                                                     │
              ┌──────────────────────────────────────┼───────────────────────┐
              │                                       │                        │
        ┌─────▼──────┐                        ┌───────▼────────┐       ┌───────▼───────┐
        │ services   │                        │  LLMClient     │       │  Celery worker │
        │ oauth,gmail│                        │  (Protocol)    │       │  sync_user     │
        │ ingestion, │                        │   └ Anthropic  │       └───────┬───────┘
        │ extraction,│                        │     provider   │               │
        │ priority,  │                        └────────────────┘               │
        │ today      │                                                          │
        └─────┬──────┘                                                          │
              │                                                                 │
        ┌─────▼─────────────────── Postgres (pgvector) ──────────────────┐      │
        │ users · connected_accounts · messages · calendar_events ·      │◄─────┘
        │ commitments · tasks · draft_replies · action_proposals ·       │
        │ execution_logs                                                 │
        └────────────────────────────────────────────────────────────────┘
        Redis ── Celery broker + result backend
```

## Backend layering

Routes → services → models. Routes are thin: they authenticate, call a service, and
shape the response. Business logic lives in `app/services`. The AI pipeline maps to the
PRD's agent model (section 14.1):

- **Ingestion** (`services/ingestion.py`) — agent 1. Pulls Gmail, normalizes, dedupes.
- **Extraction** (`services/extraction.py`) — agent 2. Classifies and extracts commitments.
- **Priority** (`services/priority.py`) — agent 3. Transparent weighted scoring with reasons.
- **Today** (`services/today.py`) — assembles the dashboard.
- **Execution** (`api/v1/actions.py::_execute`) — agent 8. Pushes approved Gmail drafts.
- **Safety/Approval** (`ActionProposal` + the actions routes) — agent 9. Gates level-3 actions.

Drafting, planning, meeting-prep, and memory agents are defined in the LLM interface or
deferred (see TODO).

## Key decisions

### Provider-agnostic LLM layer

App services depend on `app.llm.base.LLMClient` (a `Protocol`), never on a vendor SDK.
The Anthropic implementation is the only place `anthropic` is imported
(`app/llm/providers/anthropic_client.py`). Structured extraction uses tool-use: the
target Pydantic model's JSON schema becomes a forced tool, and the tool input is
validated back into the model. System prompts are marked cache-eligible so a sync batch
reuses the prompt prefix. Adding OpenAI or Mistral means writing one new provider module
and a branch in `app/llm/__init__.py`.

### Model strategy

Per PRD 14.2, classification uses a cheap model (`claude-haiku-4-5`) and extraction and
drafting use a stronger one (`claude-sonnet-4-6`). The priority engine is rules-based and
deterministic, not an LLM call, so rankings are debuggable and explainable.

### Privacy by storage minimization

Raw email bodies are never persisted. Ingestion stores a snippet and metadata; the
extraction pipeline fetches the full body from Gmail in-process and discards it. OAuth
tokens are encrypted with Fernet (`services/crypto.py`) before they touch Postgres. See
SECURITY.md.

### The approval spine

Internal preparation (creating a draft, classifying, extracting) is risk level 1 and
needs no approval. Anything that touches the outside world is level 3+ and must exist as
an `ActionProposal`, be approved, then produce an `ExecutionLog`. The slice's one
external action is pushing a draft into Gmail. Sending email outright is deliberately not
built: it needs the `gmail.send` scope and stronger confirmation.

### Data model scope

Only the entities the slice touches are modeled: `User`, `ConnectedAccount`, `Message`,
`CalendarEvent`, `Commitment`, `Task`, `DraftReply`, `ActionProposal`, `ExecutionLog`.
The PRD's `Person`, `Project`, and `DailyBriefing` entities are deferred until the
features that need them land. Calendar events are ingested into the model now so
meeting-prep can build on them without a re-sync, but no calendar-driven features ship in
the slice.

### Sync is synchronous now, async-ready

`POST /api/v1/sync` runs ingestion and extraction inline so the slice is easy to demo end
to end. The same logic is wrapped in a Celery task (`app/workers/tasks.py::sync_user`) for
the production path, where ingestion runs off the request and on a schedule.

## Shared types

`packages/shared-types` mirrors the backend enums and DTOs in TypeScript. It is the single
source the mobile app imports. When a backend schema changes, update the mirror. There is
no codegen yet; see TODO for the OpenAPI-to-types follow-up.
