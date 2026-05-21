# TODO

What is built, what is deferred, and what is deliberately out of scope. Ordered by what
the slice needs next to become a real beta.

## Built (the slice foundation)

- [x] Monorepo: backend (FastAPI), mobile (Expo), shared-types, docs.
- [x] Postgres models for the slice + approval/audit spine.
- [x] Google OAuth (Gmail + Calendar), encrypted token storage.
- [x] Gmail ingestion (snippet + metadata, no raw bodies stored).
- [x] Classification + commitment extraction via provider-agnostic LLM layer (Anthropic).
- [x] Transparent, explainable priority engine with tests.
- [x] Today dashboard endpoint and screen.
- [x] Draft reply generation.
- [x] Approval flow: propose → approve → push Gmail draft → log.
- [x] Celery worker scaffold for background sync.
- [x] Verification green: ruff, mypy strict, pytest, tsc (shared + mobile).

## Next, to make the slice production-real

### Security (see SECURITY.md)
- [ ] OAuth access-token refresh + re-encryption on expiry.
- [ ] Bind OAuth `state` to the initiating client (PKCE-style).
- [ ] Log redaction policy: scrub email content, tokens, PII.
- [ ] Account deletion + integration revocation endpoints (PRD 12.1).
- [ ] API and Gmail-call rate limiting.
- [ ] `TOKEN_ENCRYPTION_KEY` rotation path.

### Correctness and quality
- [ ] Full-thread retrieval for drafting (slice uses the stored snippet only).
- [ ] Idempotent, incremental Gmail sync (history API / `historyId`) instead of refetch.
- [ ] Priority engine learns from user feedback (PRD 16.1); right now feedback is recorded
      via commitment status changes but not fed back into scoring.
- [ ] Integration tests against a Gmail sandbox and a test Anthropic key.
- [ ] OpenAPI-to-TypeScript codegen so `packages/shared-types` is generated, not hand-mirrored.

## Should-have (PRD 28 "Should Have", roadmap Phase 1)

- [ ] Daily briefing generation + schedule (`LLMClient.generate_daily_briefing` exists).
- [ ] Smart, batched notifications with quiet hours (PRD 12.8).
- [ ] Meeting prep (`LLMClient.summarize_meeting_context` exists; needs the screen + trigger).
- [ ] Waiting-for tracker surfaced as its own view.
- [ ] Onboarding calibration questions (PRD 9.1) writing to `User.preferences`.
- [ ] Manual task creation + voice capture.
- [ ] Push notifications.

## Later (PRD roadmap Phase 2+)

- [ ] Notion / Todoist / Slack / Google Drive integrations.
- [ ] Project grouping, people memory (the `Person`/`Project` entities).
- [ ] Subscription billing.

## Explicitly out of scope (do not build)

Per the build brief and PRD 7.2:

- Autonomous purchases, payments, banking actions.
- Uber Eats / Deliveroo / any delivery ordering.
- WhatsApp automation.
- Full browser automation.
- Legal document signing.
- Multi-user team workspace, enterprise admin console.
- Sending email outright (only Gmail-draft creation is allowed in the slice).
