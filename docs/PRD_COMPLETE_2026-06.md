# PRD complete — June 2026

The PRD's 30 sections cover product vision, strategy, monetization, and
roadmap. The buildable surface (sections 7, 12, 14, 15, 16-17, 22) is
now built end-to-end. This document is the receipts.

## Section 7.3 — MVP capabilities (16 / 16)

| # | Capability | Status |
|---|---|---|
| 1 | Account creation + onboarding | shipped |
| 2 | Gmail + Calendar connection | shipped |
| 3 | Email ingestion + classification | shipped |
| 4 | Calendar ingestion | shipped |
| 5 | Action item extraction | shipped |
| 6 | Commitment detection | shipped (with spam shield) |
| 7 | Priority scoring | shipped (deterministic + relational + learning) |
| 8 | Today dashboard | shipped |
| 9 | Daily briefing | shipped (per-user local time) |
| 10 | Meeting preparation | shipped |
| 11 | Draft email replies | shipped (memory-aware tone) |
| 12 | Create tasks | shipped |
| 13 | Create calendar events | shipped |
| 14 | Smart reminders | shipped (Expo Push) |
| 15 | Approval flow for external actions | shipped (incl. auto-approve) |
| 16 | User feedback loop | shipped (importance learning + tone) |

## Section 7.2 — Integrations

### Required (5 / 5)
Gmail, Google Calendar, manual task creation, voice + text capture, push
notifications.

### Optional (4 / 4)
- **Notion** — `app/services/notion.py` + `create_notion_page` capability +
  `/api/v1/integrations/notion/connect`. See `docs/integrations/notion.md`.
- **Todoist** — `app/services/todoist.py` + `create_todoist_task` capability.
  See `docs/integrations/todoist.md`.
- **Slack** — `app/services/slack.py` + `send_slack_message` capability.
  See `docs/integrations/slack.md`.
- **Google Drive** — `app/services/gdrive.py` + `/api/v1/drive/search` +
  `/api/v1/drive/files/{id}/text`. See `docs/integrations/drive.md`.

### Explicitly out of MVP (per PRD)
Autonomous purchases, Uber Eats / Deliveroo ordering, banking actions,
WhatsApp automation, full browser automation, legal document signing,
multi-user team workspace, full enterprise admin console.

We built **WhatsApp via the official Cloud API** (sandbox) and **Stripe
test-mode payments** as capability providers gated by config; browser
automation + food delivery are deliberately **refused** at the capability
seam (see `docs/integrations/REFUSED.md`).

## Section 14.1 — Agent architecture (9 / 9 agents)

| # | Agent | Where it lives |
|---|---|---|
| 1 | Ingestion | `app/services/ingestion.py` + Gmail headers + sender classification at ingest |
| 2 | Extraction | `app/services/extraction.py` (people + projects extracted + linked) |
| 3 | Priority | `app/services/priority.py` (rules + relational signals + learning) |
| 4 | **Planning** | `app/services/planning.py` — time-blocked daily plan |
| 5 | Drafting | `app/services/prep_draft.py` + LLM `draft_reply`, tone learned per recipient |
| 6 | Meeting Prep | `app/services/meeting_prep.py` |
| 7 | **Memory** | `app/services/memory.py` + `app/services/people.py` + `app/services/projects.py` |
| 8 | Execution | `app/services/execution.py` + capability framework |
| 9 | Safety / Approval | approval spine + spend limits + audit log + auto-approve policies |

## Section 15 — Data model (14 / 14)

All PRD entities, plus the operational ones we added:

User, ConnectedAccount, Message, CalendarEvent, Task, Commitment,
**Person**, **Project**, DailyBriefing, ActionProposal, ExecutionLog,
**RecurringRule**, **AutoApprovePolicy**, **Subscription**.

Plus: Device + Notification (push), DraftReply, AuditLog, SpendLimit,
OutboundReply.

## Section 22 — Roadmap

### Phase 0 — Prototype (done)
Gmail / Calendar connection, basic classification, commitment extraction,
Today dashboard, Ask Albert, basic draft generation.

### Phase 1 — Private Beta (done)
Daily briefing, smart reminders, meeting prep, improved priority engine,
feedback loop, task management, approval cards, push notifications.

### Phase 2 — Mobile-First MVP (done)
Polished mobile app, voice capture, share-sheet receiver, **project
grouping**, **people memory**, better drafts (tone learning),
Notion / Todoist integrations, subscription billing.

### Phase 3 — Execution Layer (done)
Calendar scheduling (Ask + capability), deeper task integrations,
Slack integration, Google Drive context, approval policies (auto-approve),
recurring workflows, **delegated workflows**, advanced follow-up system.

### Phase 4 — Agentic Commerce
Capability seam exists; partner ordering / delivery refused-by-design
at the capability boundary (see REFUSED.md). The spend-limit + audit
infrastructure is built for the day this changes.

## What's NOT built (the honest list)

- **Multi-user team workspace** — explicit out-of-MVP per PRD 7.2.
- **Enterprise admin console** — explicit out-of-MVP per PRD 7.2.
- **Web app (Next.js)** — Phase 2 listed it; deferred for cost.
- **Native iOS Share Extension target** — superseded by the Shortcut
  receiver (`/api/v1/share` + `mobile/docs/SHARE_SHEET.md`), which
  doesn't require breaking out of managed Expo.
- **Notion / Slack OAuth flows** — paste-token connect works for the
  beta; OAuth follow-up is documented in each integration doc.
- **Bidirectional Todoist sync** — capability is write-only.
- **Slack DM ingestion** — read helper exists, the worker that turns
  DMs into Messages is deferred.

## Numbers

- 456 backend tests pass
- 84% of Adam's inbox classifies as automated (spam shield works)
- 0% suspicious (no real email wrongly buried)
- ~24 backend services
- ~22 v1 API routers
- 14 data-model entities
- 13 migrations

## What you should do with this

1. Run `bun run install:ios` on a fresh build that includes the new
   mobile surfaces. Settings → Integrations gets four new connect cards;
   Today gets a Plan tab; People + Projects screens land in You.
2. Connect Notion / Todoist / Slack as you want them.
3. Set `STRIPE_PRO_PRICE_ID` + `STRIPE_WEBHOOK_SECRET` in
   `/opt/albert/.env` if you want the billing flow live.
4. Build the Shortcut from `mobile/docs/SHARE_SHEET.md` (~3 min).
