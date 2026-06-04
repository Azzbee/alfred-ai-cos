"""Sender classification — the spam shield in front of the priority ranker.

The ranker can be brilliant about deadlines and VIPs, but if a Mailchimp
"URGENT: Your subscription expires today" leaks through as a `person` sender,
the user gets a critical-priority push for marketing. That is the failure
mode this module exists to prevent.

Classification is deterministic and runs at ingest time, so per-commitment
scoring is O(1) and the ranker can hard-floor priority for anything that
isn't a real person. Seven classes:

    person       — a real human writing personally. Eligible for any
                   priority including critical.
    role_account — info@, support@, team@, hello@. Often a real human
                   replies, but the address is shared. Capped at high.
    automated    — newsletters, transactional, notifications, marketing.
                   Capped at low. Cannot get the critical push.
    bulk         — same as automated but the message itself carries
                   bulk-mail headers (List-Unsubscribe / Precedence: bulk).
                   Treated identically to automated for scoring.
    suspicious   — display-name/domain mismatch, urgency-spam patterns,
                   blacklisted sender domains. Capped at noise.
    vip          — user has explicitly marked this sender as VIP.
                   Promoted: any score >= a threshold becomes high.
    muted        — user has explicitly muted this sender. Equivalent to
                   automated (capped at low), regardless of content.

The user can override any classification through user.preferences:
    {"sender_overrides": {"vip": ["mary@buyer.co"], "muted": ["news@x.io"]}}

VIP/muted overrides win over every other signal so the user can correct
the rare misclassification without arguing with a black-box model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.db.models import Message, User

SenderClass = Literal[
    "person",
    "role_account",
    "automated",
    "transactional_critical",
    "bulk",
    "suspicious",
    "vip",
    "muted",
]


@dataclass
class Classification:
    """The classifier's verdict on one message.

    `cls` is the bucket. `reasons` lists the human-readable signals that drove
    the decision — surfaced in the Today screen's `reason` string so the user
    can see WHY something is or isn't shown."""

    cls: SenderClass
    reasons: list[str] = field(default_factory=list)


# --- email parsing ---

_EMAIL_RE = re.compile(r"<([^>]+)>|([\w.+-]+@[\w-]+\.[\w.-]+)")


def parse_address(raw: str) -> tuple[str, str]:
    """Split 'Mary Smith <mary@x.co>' into (display_name, email). Either side
    can be empty when the input is malformed. Email is lowercased."""
    if not raw:
        return ("", "")
    m = _EMAIL_RE.search(raw)
    email = ""
    if m:
        email = (m.group(1) or m.group(2) or "").lower()
    display = raw
    if "<" in raw:
        display = raw.split("<", 1)[0].strip().strip('"').strip()
    elif email:
        display = ""
    return (display, email)


def domain_of(email: str) -> str:
    """Return the domain portion of an email, lowercased. Empty when no @."""
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower()


# --- role / automated patterns ---

# Local parts that strongly suggest a shared-inbox role account, not a person.
_ROLE_LOCAL_PARTS = {
    "info",
    "hello",
    "hi",
    "team",
    "support",
    "help",
    "contact",
    "admin",
    "office",
    "sales",
    "billing",
    "accounts",
    "accounting",
    "hr",
    "people",
    "careers",
    "jobs",
    "press",
    "media",
    "legal",
    "compliance",
    "privacy",
    "security",
    "abuse",
    "postmaster",
    "webmaster",
}

# Local parts that are almost always automated mailers. These can never be
# `person` regardless of content.
_AUTOMATED_LOCAL_PARTS = {
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "notifications",
    "notification",
    "alerts",
    "alert",
    "updates",
    "update",
    "newsletter",
    "newsletters",
    "digest",
    "weekly",
    "daily",
    "mailer",
    "mailman",
    "bounces",
    "mailer-daemon",
    "marketing",
    "promo",
    "promotions",
    "campaigns",
    "deals",
    "offers",
    "news",
    "feedback",
    "reply",  # reply@<service>.com is usually a tracker
    "automated",
    "auto",
    "system",
    "robot",
    "bot",
    "transactional",
    "receipts",
    "receipt",
    "billing-noreply",
    "invitations",
    "invites",
}

# Local parts that have a digit suffix typical of mail-blast platforms:
# bounce-12345@sender.mailchimpapp.com, click@email.something.io, etc.
_AUTOMATED_LOCAL_PREFIXES = (
    "bounce",
    "bounces",
    "click",
    "open",
    "track",
    "tracking",
    "campaign",
    "blast",
    "mail-",
    "list-",
    "store-",  # store-news@amazon.com
)

# Suffix patterns: a local part ending in any of these is automated even if
# the prefix is generic. Catches messages-noreply@linkedin.com,
# editors-noreply@linkedin.com, billing-noreply@stripe.com,
# notifications-noreply, etc.
_AUTOMATED_LOCAL_SUFFIXES = (
    "-noreply",
    "-no-reply",
    "-donotreply",
    "-do-not-reply",
    "-notifications",
    "-notification",
    "-alerts",
    "-news",
    "-newsletter",
    "-mailer",
    "-marketing",
    "-campaign",
    "-promo",
    "-digest",
    "-bounces",
    "-updates",
    ".noreply",  # no.reply.alerts@chase.com
    ".no-reply",
)

# Domain patterns that are bulk-mail platforms — anything sent from these is
# automated regardless of local part.
_BULK_DOMAIN_PATTERNS = (
    "mailchimp",
    "mailchimpapp",
    "facebookmail.com",  # Facebook's mailer; legitimate per brand-domain list
    "instagrammail.com",
    "medallia.com",  # feedback / survey blasts
    "qualtrics.com",
    "surveymonkey.com",
    "typeform.com",
    "mailerlite",
    "mlbemail.com",  # MLB sports marketing
    "yotpo",
    "iterable",
    "braze.com",
    "marketo",
    "pardot.com",
    "eloqua.com",
    "mailgun",
    "mandrillapp",
    "sendgrid",
    "sendgrid.net",
    "amazonses",
    "amazon.com.dwbrmq",  # AWS bounce subdomain
    "constantcontact",
    "campaignmonitor",
    "createsend.com",
    "klaviyo",
    "klaviyomail",
    "convertkit",
    "mailerlite",
    "drip.com",
    "hubspot",
    "hsforms",
    "intercom-mail",
    "intercom.me",
    "customer.io",
    "postmarkapp",
    "mailjet",
    "smtp2go",
    "sparkpost",
    "salesforce.com",  # SFMC sends
    "salesloft",
    "outreach.io",
    "apollo.io",
    "lemlist",
    "substack.com",
    "convertkit-mail",
    "mailpoet.com",
    "tinyletter",
    "groovehq",
)

# Common bulk-mail subdomain prefixes: e.g. email.notion.com, news.airbnb.com,
# updates.github.com. These often deliver legitimate transactional mail too,
# so this knocks the class down to automated rather than spam.
_TRANSACTIONAL_SUBDOMAINS = (
    # Single-letter / abbreviation prefixes commonly used by ESPs to obscure
    # that the mail is bulk: em.linkedin.com, e.zoom.us, eg.expedia.com.
    "e.",
    "em.",
    "ec.",
    "eg.",
    "ep.",
    "eu.",
    "ms.",
    "mt.",
    "mx.",
    "mk.",
    "n.",
    "p.",
    "t.",
    # Letter prefixes used by ESPs as throwaway subdomains:
    # b.express.com, s.shopify.com, h.brand.com.
    "a.",
    "b.",
    "c.",
    "d.",
    "f.",
    "g.",
    "h.",
    "k.",
    "l.",
    "m.",
    "o.",
    "r.",
    "s.",
    "u.",
    "v.",
    "w.",
    "x.",
    "y.",
    "z.",
    # Two-letter brand-mailing prefixes
    "hi.",
    "go.",
    # Word prefixes
    "email.",
    "emails.",
    "enews.",
    "news.",
    "newsletter.",
    "marketing.",
    "promo.",
    "promotions.",
    "offers.",
    "info.",
    "mail.",
    "mailing.",
    "mailings.",
    "send.",
    "sender.",
    "delivery.",
    "deliver.",
    "smtp.",
    "notify.",
    "notifications.",
    "notification.",
    "alerts.",
    "alert.",
    "messages.",
    "message.",
    "link.",
    "links.",
    "trk.",
    "track.",
    "tracking.",
    "click.",
    "campaign.",
    "campaigns.",
    "store-news.",
    "updates.",
    "update.",
    "events.",
    "post.",  # info@post.tommy.com pattern
    "broadcast.",
    "deals.",
    "digest.",
    "weekly.",
    "daily.",
)

# Free-mail providers that DO host real people. Used to skip the "no first.last
# pattern → role account" guess for personal Gmail/Yahoo/etc.
_FREE_MAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.fr",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "fastmail.com",
    "gmx.com",
    "aol.com",
    "qq.com",
    "163.com",
    "126.com",
    "yandex.com",
}

# Domains that have been documented to act as launchpads for phishing or
# extreme low-trust outreach. Anything from these is `suspicious` unless the
# user has VIP-ed it.
_SUSPICIOUS_DOMAINS = {
    "sendinblue.com",  # legitimate bulk + frequently abused
    "tutanota.com",  # often used for cold outreach
    "mail.ru",
    "yandex.ru",
}


# Verified-issuer root domains for transactional_critical. A message can only
# be promoted to transactional_critical when its sender's root domain is in
# this set AND its subject matches a critical-action pattern. This combo
# blocks the obvious phishing exploit (claiming to be Stripe from
# stripe-secure.tk) because the domain check is strict and pre-empts the
# brand-impersonation check.
_VERIFIED_TRANSACTIONAL_ISSUERS = {
    # Payments / billing
    "stripe.com",
    "paypal.com",
    "square.com",
    "squareup.com",
    "intuit.com",
    "quickbooks.com",
    "wise.com",
    "revolut.com",
    "ramp.com",
    "brex.com",
    "mercury.com",
    "chase.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "citi.com",
    "hsbc.com",
    "barclays.com",
    "americanexpress.com",
    "amex.com",
    "capitalone.com",
    # Cloud / infra (failed payments, expiring credit cards, deletion notices)
    "aws.amazon.com",
    "amazonaws.com",
    "google.com",
    "googlecloud.com",
    "cloud.google.com",
    "microsoft.com",
    "azure.com",
    "digitalocean.com",
    "linode.com",
    "vercel.com",
    "netlify.com",
    "hetzner.com",
    "cloudflare.com",
    # Identity / compliance
    "docusign.com",
    "hellosign.com",
    "dropboxsign.com",
    "okta.com",
    "auth0.com",
    "1password.com",
    "lastpass.com",
    # Government — anything ending in .gov / .gov.uk / similar is added by
    # suffix check, see _is_government_domain below.
}


# Subject patterns that ARE legitimately critical. Each must combine WITH a
# verified-issuer domain. A subject alone never triggers this class — a
# personal email that happens to say "payment failed" is still personal.
_TRANSACTIONAL_CRITICAL_SUBJECTS = re.compile(
    r"\b("
    r"(payment|charge|transfer) (failed|declined|reversed|disputed)|"
    r"insufficient funds|"
    r"card (expired|expiring|declined)|"
    r"account (suspended|locked|closed|on hold|frozen|deactivated|will be)|"
    r"action required (today|now|by|before|to)|"
    r"final notice (before|to|of)|"
    r"(verification|identity) (required|needed|pending|on hold)|"
    r"(deletion|cancellation) scheduled|"
    r"(invoice|subscription) (overdue|past due|unpaid)|"
    r"(security|fraud) alert|"
    r"(unusual|suspicious) (login|sign[- ]?in|activity) (detected|from)|"
    r"document (ready|awaiting) (to sign|signature)|"
    r"signature requested|"
    r"please sign|"
    r"data breach|"
    r"production (outage|incident)|"
    r"sla (breach|miss)"
    r")\b",
    re.IGNORECASE,
)


def _root_domain(dom: str) -> str:
    """Reduce 'email.notifications.stripe.com' to 'stripe.com'. Naive: just
    the last two labels. Good enough for the verified-issuer match because
    every issuer in the list is a 2-label registered domain."""
    parts = dom.split(".")
    if len(parts) < 2:
        return dom
    # Handle the common 2-part TLDs we care about (.co.uk, .gov.uk, .com.au).
    if len(parts) >= 3 and ".".join(parts[-2:]) in {
        "co.uk",
        "gov.uk",
        "ac.uk",
        "com.au",
        "co.jp",
        "com.br",
    }:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _is_government_domain(dom: str) -> bool:
    """Government domains globally. These can be transactional_critical when
    paired with an action subject — a real IRS / HMRC notice is important."""
    if not dom:
        return False
    return (
        dom.endswith(".gov")
        or dom.endswith(".gov.uk")
        or dom.endswith(".gov.au")
        or dom.endswith(".gouv.fr")
        or dom.endswith(".gob.es")
        or dom.endswith(".gc.ca")
        or dom.endswith(".gov.in")
        or dom.endswith(".gov.sg")
    )


def _is_transactional_critical(*, dom: str, subject: str | None) -> bool:
    """A message is transactional_critical when its root domain is on the
    verified-issuer list (or is a government domain) AND its subject matches
    a critical-action pattern. Both checks required — defends against
    impersonation."""
    if not subject:
        return False
    root = _root_domain(dom)
    in_issuer_list = (
        root in _VERIFIED_TRANSACTIONAL_ISSUERS
        or dom in _VERIFIED_TRANSACTIONAL_ISSUERS
        or _is_government_domain(dom)
    )
    if not in_issuer_list:
        return False
    return bool(_TRANSACTIONAL_CRITICAL_SUBJECTS.search(subject))


# --- header signals ---


def _has_bulk_headers(headers: dict | None) -> tuple[bool, list[str]]:
    """Return (is_bulk, reasons). Bulk = the message itself ANNOUNCES it's bulk
    mail via standard headers. RFC 2076 + Microsoft conventions covered."""
    if not headers:
        return (False, [])
    h = {k.lower(): str(v) for k, v in headers.items()}
    found: list[str] = []
    if h.get("list-unsubscribe"):
        found.append("List-Unsubscribe header present")
    precedence = h.get("precedence", "").lower()
    if precedence in {"bulk", "junk", "list"}:
        found.append(f"Precedence: {precedence}")
    auto_submitted = h.get("auto-submitted", "").lower()
    if auto_submitted and auto_submitted != "no":
        found.append(f"Auto-Submitted: {auto_submitted}")
    if h.get("x-auto-response-suppress"):
        found.append("X-Auto-Response-Suppress set")
    if h.get("feedback-id"):
        found.append("Feedback-ID set (bulk delivery report)")
    if h.get("x-mailchimp-id") or h.get("x-mc-user"):
        found.append("Mailchimp delivery")
    if h.get("x-sg-eid") or h.get("x-sendgrid-id"):
        found.append("SendGrid delivery")
    if h.get("x-campaign") or h.get("x-campaign-id"):
        found.append("Campaign header")
    return (bool(found), found)


# --- subject heuristics ---

_URGENCY_SPAM_RE = re.compile(
    r"\b(ACT NOW|LIMITED TIME|FINAL NOTICE|DON'?T MISS|LAST CHANCE|"
    r"CLAIM (YOUR|NOW)|FREE|CONGRATULATIONS|YOU'?VE WON|WINNER|"
    r"VERIFY (YOUR|YOU)|SUSPEND(ED)?|UNUSUAL ACTIVITY|"
    r"UNUSUAL SIGN-?IN|CLICK HERE|EXCLUSIVE OFFER)\b",
    re.IGNORECASE,
)

# Out-of-office / auto-reply subjects. These should classify as automated
# regardless of who sent them — auto-replies are by definition not a real
# human writing personally. Covers English + French + Spanish + German.
_AUTO_REPLY_SUBJECT_RE = re.compile(
    r"^\s*("
    r"out of (the )?office|"
    r"automatic(ally)? (reply|response|generated)|"
    r"auto[- ]?(reply|response|generated|antwort|reply:)|"
    r"r[ée]ponse automatique|"
    r"respuesta automática|"
    r"abwesenheits(notiz|nachricht)|"
    r"away from"
    r")",
    re.IGNORECASE,
)


_NEWSLETTER_SUBJECT_RE = re.compile(
    # Matches several common newsletter / digest subject shapes:
    #   [Anything Newsletter] Whatever
    #   [Anything Digest] Whatever
    #   [Brand] Digest — June 4
    #   Your weekly digest from X
    #   The Daily Brief
    #   Issue #42 of the Brand
    r"(^\s*\[[^\]]*\]\s+(digest|newsletter|brief|recap|round[- ]?up)\b|"
    r"\[[^\]]*(newsletter|digest)\]|"
    r"your (weekly|daily|monthly|biweekly) (digest|update|recap|brief)|"
    r"this week (in|at)|weekly (round-?up|brief)|"
    r"the (daily|weekly|morning|evening) (brief|digest)|"
    r"^issue #?\d+|"
    r"^\s*(newsletter|digest):)",
    re.IGNORECASE,
)

# Subjects that scream "transactional, not a person": receipts, account
# notifications, security alerts.
_TRANSACTIONAL_SUBJECT_RE = re.compile(
    r"\b(your (order|receipt|invoice|statement|subscription)|"
    r"order #?\d+|receipt #?\d+|payment (received|confirmed|failed)|"
    r"your (login|sign-?in|account)|new sign-?in|password (was|reset)|"
    r"welcome to|getting started with|here'?s your)\b",
    re.IGNORECASE,
)


# --- the classifier ---


@dataclass
class _Overrides:
    vip: set[str]
    muted: set[str]


def _overrides_from(user: User | None) -> _Overrides:
    """Pull per-user overrides from user.preferences. Schema:
        preferences.sender_overrides = {"vip": [...], "muted": [...]}
    Both lists hold lowercased email addresses or bare domains. A domain
    override matches everyone at that domain — useful for "always VIP
    everyone @board.co" or "always mute everyone @news.io"."""
    if user is None:
        return _Overrides(vip=set(), muted=set())
    raw = (user.preferences or {}).get("sender_overrides") or {}
    vip = {str(s).lower().strip() for s in (raw.get("vip") or []) if s}
    muted = {str(s).lower().strip() for s in (raw.get("muted") or []) if s}
    return _Overrides(vip=vip, muted=muted)


def _matches_override(email: str, overrides: set[str]) -> bool:
    """Email matches an override if it's either an exact address match or its
    domain matches a domain-only override entry."""
    if not email:
        return False
    if email in overrides:
        return True
    dom = domain_of(email)
    if not dom:
        return False
    if dom in overrides:
        return True
    # Match subdomains too: a `*.board.co` style is implied by the bare domain.
    return any(dom.endswith("." + o) for o in overrides if "." in o)


def classify(
    *,
    sender: str,
    subject: str | None,
    snippet: str | None,
    headers: dict | None,
    user: User | None = None,
) -> Classification:
    """Pure function: return a Classification given the message's surface.

    Order of decisions (intentional, the highest-confidence signals first):

    1) user override → vip / muted (always wins)
    2) suspicious patterns: display/email mismatch, scam subject, blacklist
    3) bulk headers present → bulk
    4) automated local part OR automated platform domain → automated
    5) transactional subject + transactional subdomain → automated
    6) role local part → role_account
    7) urgency-spam subject from non-VIP first-time sender → suspicious
    8) otherwise → person

    The list of reasons accumulates regardless of which branch wins so the
    surface reason can read "marked as VIP; would otherwise be a newsletter."
    """
    display, email = parse_address(sender or "")
    dom = domain_of(email)
    overrides = _overrides_from(user)
    reasons: list[str] = []

    # 1) user overrides win first.
    if _matches_override(email, overrides.muted):
        return Classification(cls="muted", reasons=["you muted this sender"])
    if _matches_override(email, overrides.vip):
        return Classification(cls="vip", reasons=["you marked this sender VIP"])

    # 2) Hard-blacklist + brand impersonation. These are FRAUD signals — they
    # take precedence over everything else because they're independent of
    # whether the sender is bulk: a sendinblue email is suspicious AND a
    # Mailchimp blast pretending to be PayPal is also suspicious.
    if dom in _SUSPICIOUS_DOMAINS:
        return Classification(
            cls="suspicious", reasons=[f"sender domain {dom} is on the suspicious list"]
        )
    if display:
        brand = _impersonated_brand(display, dom)
        if brand:
            return Classification(
                cls="suspicious",
                reasons=[f"display name claims '{brand}' but the email domain is {dom}"],
            )
    # Phishing snippet from a no-display-name sender — actual phishing.
    if snippet and _is_phishy_snippet(snippet) and (not display or dom == ""):
        return Classification(
            cls="suspicious", reasons=["phishing-style content from a no-name sender"]
        )

    # 3) transactional_critical: a verified-issuer domain with a critical-
    # action subject. Stripe failed-payment, AWS service deletion notice,
    # DocuSign signature requested, IRS notice. Must run BEFORE the bulk-
    # headers and automated-local-part rules because legitimate Stripe
    # alerts ARE sent via SendGrid with automated local parts. The strict
    # domain check (root in verified-issuer list OR government suffix)
    # prevents phishers from claiming "Stripe failed payment" from a
    # look-alike domain.
    if _is_transactional_critical(dom=dom, subject=subject):
        reasons.append(f"verified-issuer ({_root_domain(dom)}) with critical-action subject")
        return Classification(cls="transactional_critical", reasons=reasons)

    # 4) bulk headers.
    is_bulk, bulk_reasons = _has_bulk_headers(headers)
    if is_bulk:
        return Classification(cls="bulk", reasons=bulk_reasons)

    # 5) automated local part or platform domain.
    local = email.split("@", 1)[0] if "@" in email else ""
    # Normalize dots → dashes so suffix patterns catch dot-separated locals
    # like no.reply.alerts@chase.com (→ no-reply-alerts, ends in -alerts).
    local_norm = local.replace(".", "-")
    if (
        local in _AUTOMATED_LOCAL_PARTS
        or local_norm in _AUTOMATED_LOCAL_PARTS
        or any(local.startswith(p) for p in _AUTOMATED_LOCAL_PREFIXES)
        or any(local_norm.startswith(p) for p in _AUTOMATED_LOCAL_PREFIXES)
        or any(local.endswith(s) for s in _AUTOMATED_LOCAL_SUFFIXES)
        or any(local_norm.endswith(s) for s in _AUTOMATED_LOCAL_SUFFIXES)
    ):
        reasons.append(f"sender local part '{local}' is an automated address")
        return Classification(cls="automated", reasons=reasons)
    if dom and any(p in dom for p in _BULK_DOMAIN_PATTERNS):
        reasons.append(f"sent through a bulk-mail platform ({dom})")
        return Classification(cls="automated", reasons=reasons)

    # 6) transactional / marketing subdomain → automated. A long tail of
    # marketing-specialized subdomains (em., eg., enews., offers., promo.,
    # store-news., link., trk., e.) and the EXPECTED case for any of them
    # is bulk mail. A real human emailing from a subdomain like that is
    # overwhelmingly rare; if it ever happens, the user can VIP-override.
    if dom and any(dom.startswith(prefix) for prefix in _TRANSACTIONAL_SUBDOMAINS):
        reasons.append(f"sent from transactional / marketing subdomain ({dom})")
        return Classification(cls="automated", reasons=reasons)

    # 7a) Auto-reply / out-of-office → automated. A real human's name might
    # appear in the From, but the message IS automated by definition.
    if subject and _AUTO_REPLY_SUBJECT_RE.search(subject):
        reasons.append("auto-reply / out-of-office subject")
        return Classification(cls="automated", reasons=reasons)

    # 7b) Newsletter / digest subjects from any sender → automated.
    if subject and _NEWSLETTER_SUBJECT_RE.search(subject):
        reasons.append("subject reads as a newsletter / digest")
        return Classification(cls="automated", reasons=reasons)

    # 8) role local part.
    if local in _ROLE_LOCAL_PARTS:
        reasons.append(f"shared-inbox local part '{local}'")
        return Classification(cls="role_account", reasons=reasons)

    # 9) All-caps screaming subject from a sender that PASSED every bulk /
    # automated filter — i.e., looks personal but writes like a spammer.
    # Treat as suspicious because that's almost always phishing/scam.
    if subject and _is_screaming(subject):
        return Classification(cls="suspicious", reasons=["subject is all-caps / screaming"])

    # 10) urgency-spam phrasing from a personal-looking sender — same
    # reasoning as 9. Verify-your-account from a real-looking address is
    # phishing.
    if subject and _URGENCY_SPAM_RE.search(subject):
        reasons.append("urgency-spam phrasing in the subject")
        return Classification(cls="suspicious", reasons=reasons)

    # 8) default: assumed to be a person.
    return Classification(cls="person", reasons=reasons or ["normal sender pattern"])


# Reduce a display name to a key, then compare against domain. A display name
# that claims "PayPal" must come from a paypal.com address; otherwise it's
# impersonation. The list is intentionally short — only obvious global brands
# people get phished about.
_IMPERSONATED_BRANDS: dict[str, tuple[str, ...]] = {
    # Each brand maps to a tuple of legitimate sending domains. Many large
    # brands use a dedicated mailing domain (facebookmail.com, mlbemail.com,
    # tmomail.net) that isn't the main brand's website domain.
    "paypal": ("paypal.com",),
    "stripe": ("stripe.com",),
    "google": ("google.com", "googlemail.com", "accounts.google.com"),
    "gmail": ("google.com", "googlemail.com"),
    "microsoft": ("microsoft.com", "microsoftonline.com", "office.com"),
    "apple": ("apple.com", "icloud.com", "me.com"),
    "icloud": ("apple.com", "icloud.com"),
    "amazon": ("amazon.com", "amazonses.com", "marketplace.amazon.com"),
    "facebook": ("facebook.com", "facebookmail.com", "fb.com"),
    "meta": ("fb.com", "facebookmail.com", "meta.com"),
    "instagram": ("instagram.com", "mail.instagram.com", "facebookmail.com"),
    "twitter": ("twitter.com", "x.com"),
    "x corp": ("x.com",),
    "linkedin": ("linkedin.com",),
    "github": ("github.com",),
    "dropbox": ("dropbox.com", "dropboxmail.com"),
    "docusign": ("docusign.com", "docusign.net"),
    "intuit": ("intuit.com",),
    "irs": ("irs.gov",),
    "hmrc": ("hmrc.gov.uk", "tax.service.gov.uk"),
}


def _impersonated_brand(display: str, dom: str) -> str | None:
    """If display name claims a famous brand and the domain isn't one of
    that brand's known sending domains (or a subdomain of one), return the
    brand name. Else None."""
    if not display or not dom:
        return None
    lc = display.lower()
    for brand, real_doms in _IMPERSONATED_BRANDS.items():
        if brand in lc:
            for real_dom in real_doms:
                if dom == real_dom or dom.endswith("." + real_dom):
                    return None  # legitimate
            return brand
    return None


def _is_screaming(subject: str) -> bool:
    """≥70% uppercase letters AND ≥8 letters AND no Re:/Fwd: prefix."""
    letters = [c for c in subject if c.isalpha()]
    if len(letters) < 8:
        return False
    if subject.lower().startswith(("re:", "fwd:", "fw:")):
        return False
    upper = sum(1 for c in letters if c.isupper())
    return (upper / len(letters)) >= 0.7


_PHISH_RE = re.compile(
    r"\b(verify your (account|identity|login)|click (here|the link) (to|now)|"
    r"unlock your account|your account (has been|will be) (locked|suspended|closed)|"
    r"confirm your (password|details)|update your (payment|billing) (info|details)|"
    r"wire (this|the) (funds|payment)|unusual sign-?in|"
    r"action required (today|now|immediately))",
    re.IGNORECASE,
)


def _is_phishy_snippet(snippet: str) -> bool:
    return bool(_PHISH_RE.search(snippet))


# --- attach to a Message ---


def classify_message(message: Message, *, user: User | None) -> Classification:
    """Classify a Message using its stored fields. Convenience wrapper for the
    ingestion pipeline so it doesn't unpack the message dict by hand."""
    return classify(
        sender=message.sender or "",
        subject=message.subject,
        snippet=message.snippet,
        headers=message.headers,
        user=user,
    )


# --- API for the ranker ---

# The hard floor applied to each class. A message classified as automated
# can NEVER produce a critical-priority push, no matter how many keywords
# its content matches. The user can always promote by marking the sender VIP.
PRIORITY_CEILING_FOR_CLASS: dict[SenderClass, str] = {
    "vip": "critical",  # VIPs can hit critical
    "person": "critical",  # everyone else who's a person too
    # Real failed-payment / security / signature-requested alerts from verified
    # issuers — these CAN reach critical because they have legitimate action
    # items the user must handle today (card declined, account suspended).
    "transactional_critical": "critical",
    "role_account": "high",  # shared inboxes cap at high
    "automated": "low",  # mailers can't push you
    "bulk": "low",
    "muted": "low",  # muted overrides treat like automated
    "suspicious": "noise",  # phishing / impersonation never surfaces
}


def backfill_classifications(
    db,
    *,
    user_id: str | None = None,
    batch_size: int = 500,
    force: bool = False,
) -> int:
    """Classify Messages and write Message.sender_classification.

    Default (force=False): only touch rows where sender_classification IS NULL.
    Used after adding the column or after re-ingesting old messages.

    force=True: re-classify EVERY row. Used after the classifier itself gets
    smarter and we want existing rows to pick up the new rules without a
    full re-ingest.

    Both modes are safe to call repeatedly. Returns the number of messages
    classified in this run."""
    from sqlalchemy import select  # local import: keeps `sender_class` framework-free

    from app.db.models import Message, User

    classified = 0
    # Keyset pagination by id so force=True doesn't infinite-loop on rows it
    # just wrote. We always advance past the highest id we've seen.
    last_id: str | None = None
    while True:
        stmt = select(Message).order_by(Message.id).limit(batch_size)
        if not force:
            stmt = stmt.where(Message.sender_classification.is_(None))
        if user_id is not None:
            stmt = stmt.where(Message.user_id == user_id)
        if last_id is not None:
            stmt = stmt.where(Message.id > last_id)
        batch = list(db.scalars(stmt))
        if not batch:
            break
        last_id = batch[-1].id
        # Cache users per batch so we don't refetch the same user for every row.
        users: dict[str, User | None] = {}
        for m in batch:
            user = users.get(m.user_id)
            if user is None and m.user_id not in users:
                user = db.get(User, m.user_id)
                users[m.user_id] = user
            cls = classify(
                sender=m.sender or "",
                subject=m.subject,
                snippet=m.snippet,
                headers=m.headers,
                user=user,
            )
            m.sender_classification = cls.cls
            classified += 1
        db.commit()
    return classified


# Score multipliers applied to the additive bonuses inside the ranker. Even
# before the hard ceiling we shrink the bonus stack for non-person classes
# so a bulk message can't reach the score that would otherwise put it at
# medium even if all rules fire.
SCORE_MULTIPLIER_FOR_CLASS: dict[SenderClass, float] = {
    "vip": 1.15,  # mild lift for VIPs
    "person": 1.0,
    # Transactional_critical from a verified issuer is genuine urgency that
    # the user almost certainly needs to handle today — slightly lifted so
    # a "payment failed" alert with a thin LLM-extracted commitment still
    # clears the high → critical threshold.
    "transactional_critical": 1.10,
    "role_account": 0.85,
    "automated": 0.45,
    "bulk": 0.40,
    "muted": 0.20,
    "suspicious": 0.0,  # zero out — only the constant urgency reason shows
}
