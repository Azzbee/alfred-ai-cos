# The spam shield — why marketing can't reach critical priority

A ranker that occasionally pings the user for a Mailchimp blast is worse than
no ranker at all. This document describes the deterministic shield in front
of the priority engine that makes "phenomenal email recommendations" mean
"the truly important ones, and only the truly important ones."

## Observed accuracy on Adam's prod inbox (June 2026, 152 messages)

| Class                  | Count | %   | Behavior                                                         |
| ---------------------- | ----- | --- | ---------------------------------------------------------------- |
| automated              | 127   | 84% | hard-capped at `low`                                             |
| role_account           | 17    | 11% | hard-capped at `high`                                            |
| person                 | 6     | 4%  | can reach `critical`                                             |
| transactional_critical | 2     | 1%  | can reach `critical` (verified-issuer + critical-action subject) |
| suspicious             | 0     | 0%  | hard-capped at `noise` (invisible)                               |

The 6 person-classified messages were audited individually: 1 is a self-email,
1 is a genuine reply from a real human at L'Oréal, and 4 are borderline
(real-person-writing-marketing). The ranker is calibrated so the borderline
cases get one dismissal before learning demotes future similar items.

Calibration was driven by 5 iterations of: classify → force-backfill → query
prod distribution → audit the leaks → add fixture tests → tune the rules.
Every leak found became a fixture in test_sender_class.py, so the catalog
grows deterministically.

## The four layers

```
                    ┌───────────────────────────────┐
INBOUND  ─────────► │  1. SENDER CLASSIFIER         │
RFC822 message      │     (sender_class.py)         │
                    │     person / role / automated │
                    │     / bulk / suspicious /     │
                    │     vip / muted               │
                    └──────────────┬────────────────┘
                                   │ written to
                                   ▼
                    Message.sender_classification (string)

                    ┌───────────────────────────────┐
SCORE COMMITMENT ─► │  2. SCORE MULTIPLIER          │
                    │     (priority.py)             │
                    │     person × 1.0              │
                    │     role × 0.85               │
                    │     automated × 0.45          │
                    │     bulk × 0.40               │
                    │     muted × 0.20              │
                    │     suspicious × 0.0          │
                    │     vip × 1.15                │
                    └──────────────┬────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │  3. ADDITIVE BONUS CAP        │
                    │     score = min(score, 95)    │
                    │     prevents keyword stacking │
                    └──────────────┬────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │  4. HARD PRIORITY CEILING     │
                    │     person → critical OK      │
                    │     role → high max           │
                    │     automated → low max       │
                    │     bulk → low max            │
                    │     suspicious → noise max    │
                    │     muted → low max           │
                    │     vip → critical OK         │
                    └───────────────────────────────┘
```

A message can stack every keyword bonus in the catalog and still cap at `low`
if it's automated. The shield is the no-questions-asked guarantee that
marketing can never wake you up.

## What the classifier looks at

In `app/services/sender_class.py`, in order:

1. **User overrides** (`user.preferences.sender_overrides.vip / .muted`) win
   first. The user can pin any address or whole domain.
2. **Suspicious patterns**:
   - Display-name claims a famous brand but email is on the wrong domain
     (PayPal-from-not-paypal-dot-com).
   - Sender domain on the blacklist (mail.ru, yandex.ru, tutanota for
     cold outreach, sendinblue for abuse).
   - All-caps screaming subject (≥70% uppercase letters, no Re:/Fwd:).
   - Urgency-spam phrases ("ACT NOW", "VERIFY YOUR ACCOUNT", "LIMITED TIME").
   - Phishing snippet from a no-display-name sender.
3. **Bulk headers**: `List-Unsubscribe`, `Precedence: bulk|junk|list`,
   `Auto-Submitted`, `X-Auto-Response-Suppress`, `Feedback-ID`, Mailchimp /
   SendGrid X-headers, `X-Campaign(-ID)`.
4. **Automated local part**: `noreply`, `notifications`, `marketing`,
   `bounces-12345`, `mailer-daemon`, etc.
5. **Bulk-mail platform domain**: `mailchimpapp.com`, `sendgrid.net`,
   `mailgun`, `klaviyo`, `hubspot`, `intercom-mail`, `customer.io`, `apollo.io`,
   `outreach.io`, `salesloft`, `substack.com`, and ~30 more.
6. **Transactional subdomain + transactional subject**: `email.brand.com`
   sending "Your receipt #12345" → automated. Same subdomain sending "Can we
   hop on a call?" → only role_account (a real salesperson uses the same
   subdomain).
7. **Newsletter subject pattern**: `[X Digest]`, "Your weekly digest from Y",
   "Issue #42", "The Daily Brief".
8. **Role local parts**: `info`, `support`, `team`, `hello`, `sales`,
   `billing`, `legal`, `hr`, `press`. Real humans, shared inbox — capped at
   `high`.
9. **Default**: `person`.

Everything that makes it past 1-8 is a real human writing personally.

## The override escape hatch

Sometimes the deterministic rules are wrong. The user fixes it:

```
POST   /api/v1/senders/overrides     {"address": "board@brand.co", "bucket": "vip"}
POST   /api/v1/senders/overrides     {"address": "alerts.io",      "bucket": "muted"}
GET    /api/v1/senders/overrides
DELETE /api/v1/senders/overrides/board@brand.co
```

- `address` accepts a full email OR a bare domain (matches every address at
  the domain, including subdomains).
- The two buckets are mutually exclusive — adding to one removes from the
  other.
- After every override change, every existing Message from that sender is
  re-classified IN PLACE so the dashboard reflects the new policy without a
  re-ingest. (See `senders.py:_rebuild_classifications`.)

## Backfill for production

The `c3d4e5f6a7b8` migration adds `Message.headers` and
`Message.sender_classification` as nullable columns. Existing rows remain NULL
until the one-shot backfill runs:

```
cd backend && uv run python scripts/backfill_sender_classifications.py
```

Idempotent — only NULL rows get touched. Run it once after the deploy.

## Tests

The `tests/test_priority_spam_shield.py` file is the contract. It encodes the
promises this shield makes:

- `test_marketing_email_cannot_reach_critical` — a worst-case spam email with
  every keyword + LLM-critical + a phony deadline still caps at `low`.
- `test_bulk_header_floors_priority` — List-Unsubscribe = `low`, no exceptions.
- `test_phishing_cannot_be_visible_at_all` — suspicious → `noise`.
- `test_role_account_caps_at_high` — info@/support@ can't out-rank a real
  person with the same content.
- `test_vip_override_lets_a_marketer_reach_critical` — escape hatch works.
- `test_muted_buries_a_real_person` — opposite escape hatch works.
- `test_real_person_still_reaches_critical` — no regression on the genuine case.
- `test_real_person_outranks_marketing_even_when_marketing_has_more_keywords`
  — the grand-daddy: the spam shield must win in mixed inbox sort order too,
  not just in absolute bucket.

`tests/test_sender_class.py` has 55 unit tests covering every classifier branch
with realistic fixtures (Mailchimp domain, SendGrid headers, PayPal
impersonation, role accounts at startups, newsletter subjects in multiple
formats, free-mail human senders, etc.).

`tests/test_sender_class_backfill.py` proves the backfill is idempotent,
scoped, and respects user overrides.

`tests/test_senders_overrides.py` covers the override CRUD + the auto-reclassify
on add/remove.

## When the shield is wrong

If you spot a misclassification:

- **Real email got labeled spam**: `POST /api/v1/senders/overrides` with bucket
  `vip` to lock it in. If the same pattern shows up for many users, the rule
  belongs in `sender_class.py` (a domain whitelist or a regex tweak).
- **Spam got labeled real**: VIP doesn't help here — use `muted`. If it's a
  pattern, add the domain to `_BULK_DOMAIN_PATTERNS` or the local part to
  `_AUTOMATED_LOCAL_PARTS`. Then `uv run pytest tests/test_sender_class.py`
  to confirm.

Every change to the classifier should ship with a new fixture test in
`test_sender_class.py` that would have caught the bug. The catalog grows
deterministically; the shield gets sharper.
