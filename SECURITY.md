# Security

Albert reads people's email. Trust is the product (PRD principle 7). This documents what
the foundation does today and what it owes before it touches real user data at scale.

## What the slice does today

### OAuth, not passwords

Google OAuth is the only login. Albert never sees or stores a Google password. The same
consent grants Gmail and Calendar and serves as Albert's sign-in.

### Token encryption at rest

Third-party OAuth tokens are encrypted with Fernet (AES-128-CBC + HMAC) before they touch
Postgres. The key comes from `TOKEN_ENCRYPTION_KEY`. Plaintext tokens exist only in
process memory during an API call. See `backend/app/services/crypto.py` and the
`connected_accounts.token_ciphertext` column.

### Minimal scopes

The slice requests the narrowest scopes that make it work:

- `gmail.readonly` — read inbox messages.
- `gmail.compose` — create drafts. **Not** `gmail.send`. Albert cannot send mail.
- `calendar.readonly` — read events.
- `openid`, `email`, `profile` — identity.

Scopes are declared in one place: `backend/app/core/config.py::Settings.google_scopes`.

### Storage minimization

Raw email bodies are never written to the database. Ingestion stores a snippet and
metadata only; extraction fetches the full body from Gmail in-process and discards it
after classification. This keeps the most sensitive content out of the data store.

### Human-in-the-loop for external actions

No external action runs without an explicit, logged approval. Pushing a draft into Gmail
(the only external action in the slice) requires an `ActionProposal` at risk level 3, a
user approval call, and produces an append-only `ExecutionLog` row. Failures are recorded,
never silently swallowed.

### Session tokens

Albert mints its own short-lived JWT after Google login (`core/security.py`). The mobile
app stores it in the device secure store (`expo-secure-store`), not plain storage. The
client never holds the Google tokens.

## What this foundation does not yet do

These are required before a real beta, tracked in TODO.md:

- **OAuth token refresh.** The slice rebuilds credentials from the stored payload but does
  not yet refresh expired access tokens and re-encrypt them. Long-lived sessions will fail
  on expiry until this lands.
- **OAuth state binding to a device/session.** The `state` parameter is a signed,
  short-lived JWT, but it is not yet bound to the initiating client. Add PKCE-style binding.
- **Log redaction.** No structured logging policy exists yet. Before production, scrub
  email content, tokens, and PII from logs (PRD 13.2, open question 13.x).
- **Rate limiting** on the API and on Gmail calls.
- **Role-based backend access** and audit logging beyond `ExecutionLog`.
- **Account deletion and integration revocation** endpoints (PRD 12.1 requires both).
- **Key rotation** for `TOKEN_ENCRYPTION_KEY` (re-encryption path).
- **No model training on user data.** The Anthropic API is used for inference only. Make
  this an explicit, enforced policy and surface it in the privacy settings.

## Secrets

All secrets live in `.env` (gitignored). `.env.example` documents every one. Generate the
token encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never commit `.env`, service-account JSON, or any `*.pem`/`*.key`. The `.gitignore`
enforces this.

## Reporting

This is pre-beta. There is no external security contact yet. Add one
(`security@…`) and a disclosure policy before any public exposure.
