"""Tests for the sender classifier — the spam shield.

Each test exercises one realistic class of email so the suite reads like a
spec of what counts as a person, a role account, automated, bulk, or
suspicious. New observed spam patterns should land here as fixtures.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.db.models import User
from app.services import sender_class as sc


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="me@adam.dev")
    db.add(u)
    db.commit()
    return u


# --- address parsing ---


def test_parse_display_and_email() -> None:
    d, e = sc.parse_address("Mary Smith <mary@buyer.co>")
    assert d == "Mary Smith"
    assert e == "mary@buyer.co"


def test_parse_bare_email() -> None:
    assert sc.parse_address("mary@buyer.co") == ("", "mary@buyer.co")


def test_parse_quoted_display() -> None:
    d, e = sc.parse_address('"Mary Smith" <mary@buyer.co>')
    assert d == "Mary Smith"
    assert e == "mary@buyer.co"


def test_parse_lowercases_email() -> None:
    _, e = sc.parse_address("Mary <MARY@Buyer.CO>")
    assert e == "mary@buyer.co"


def test_domain_of() -> None:
    assert sc.domain_of("mary@buyer.co") == "buyer.co"
    assert sc.domain_of("garbage") == ""


# --- person: the default for normal humans ---


def test_normal_human_is_person() -> None:
    out = sc.classify(
        sender="Mary Smith <mary@buyer.co>",
        subject="Quote on the contract",
        snippet="Adam, can you send the signed contract by Friday?",
        headers={},
    )
    assert out.cls == "person"


def test_gmail_human_is_person() -> None:
    # A free-mail Gmail address with a personal display name → person.
    out = sc.classify(
        sender="Lucas Jung <lucas.jung@gmail.com>",
        subject="Re: paper draft",
        snippet="thoughts on section 4?",
        headers={},
    )
    assert out.cls == "person"


# --- role accounts ---


@pytest.mark.parametrize(
    "local",
    [
        "info",
        "support",
        "hello",
        "team",
        "contact",
        "sales",
        "billing",
        "legal",
        "hr",
        "press",
    ],
)
def test_role_local_parts(local: str) -> None:
    out = sc.classify(
        sender=f"<{local}@company.io>",
        subject="Following up",
        snippet="hi adam",
        headers={},
    )
    assert out.cls == "role_account"


# --- automated by local part ---


@pytest.mark.parametrize(
    "local",
    [
        "noreply",
        "no-reply",
        "do-not-reply",
        "notifications",
        "alerts",
        "newsletter",
        "marketing",
        "promo",
        "news",
        "digest",
        "campaigns",
        "mailer-daemon",
    ],
)
def test_automated_local_parts(local: str) -> None:
    out = sc.classify(
        sender=f"{local}@brand.io",
        subject="Your account",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


def test_automated_prefix() -> None:
    out = sc.classify(
        sender="bounce-12345@sender.mailchimpapp.com",
        subject="Open this!",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


# --- bulk by headers ---


def test_list_unsubscribe_is_bulk() -> None:
    out = sc.classify(
        sender="Sarah Updates <sarah@news.com>",
        subject="Your weekly insider digest",
        snippet="Hi readers",
        headers={"list-unsubscribe": "<https://x.io/u/1>"},
    )
    assert out.cls == "bulk"
    assert any("List-Unsubscribe" in r for r in out.reasons)


def test_precedence_bulk_is_bulk() -> None:
    out = sc.classify(
        sender="ops@something.io",
        subject="System maintenance",
        snippet="...",
        headers={"precedence": "bulk"},
    )
    assert out.cls == "bulk"


def test_auto_submitted_is_bulk() -> None:
    out = sc.classify(
        sender="bot@svc.io",
        subject="Daily report",
        snippet="...",
        headers={"auto-submitted": "auto-generated"},
    )
    assert out.cls == "bulk"


def test_feedback_id_is_bulk() -> None:
    out = sc.classify(
        sender="x@y.co",
        subject="hi",
        snippet="hi",
        headers={"feedback-id": "12345:ses-customer"},
    )
    assert out.cls == "bulk"


def test_sendgrid_header_is_bulk() -> None:
    out = sc.classify(
        sender="x@y.co",
        subject="hi",
        snippet="hi",
        headers={"x-sg-eid": "abcdef"},
    )
    assert out.cls == "bulk"


# --- automated by platform domain ---


def test_mailchimp_domain_is_automated() -> None:
    out = sc.classify(
        sender="hello@brand.us4.mailchimpapp.com",
        subject="ok",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


def test_sendgrid_domain_is_automated() -> None:
    out = sc.classify(
        sender="hello@em.sendgrid.net",
        subject="ok",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


def test_intercom_domain_is_automated() -> None:
    out = sc.classify(
        sender="Brand <hello@notifications.intercom-mail.com>",
        subject="A new feature",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


# --- newsletter subject heuristic ---


def test_newsletter_subject_is_automated() -> None:
    out = sc.classify(
        sender="newsletter@anyone.com",
        subject="Your weekly digest from Stratechery",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_digest_in_brackets_is_automated() -> None:
    out = sc.classify(
        sender="any@any.io",
        subject="[The Algorithm] Digest - June 4",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


# --- transactional subdomains ---


def test_transactional_subdomain_with_receipt_is_automated() -> None:
    out = sc.classify(
        sender="receipts@email.stripe.com",
        subject="Your receipt from Acme Co",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


def test_transactional_subdomain_is_always_automated() -> None:
    # A marketing-specialized subdomain (email., em., e., news., etc.) is
    # treated as automated regardless of subject. Real humans almost never
    # email from these subdomains; if they do, the user can VIP-override.
    # Catches LinkedIn-Ads-style senders that previously slipped to `person`.
    out = sc.classify(
        sender="Jane Doe <jane@email.startup.io>",
        subject="Can we hop on a call?",
        snippet="Hi Adam",
        headers={},
    )
    assert out.cls == "automated"


# --- suspicious ---


def test_brand_impersonation_is_suspicious() -> None:
    out = sc.classify(
        sender="PayPal <support@paypa1.scam-tld.tk>",
        subject="Re: payment",
        snippet="please verify",
        headers={},
    )
    assert out.cls == "suspicious"
    assert any("paypal" in r.lower() for r in out.reasons)


def test_legit_paypal_email_is_person() -> None:
    # If PayPal email is from paypal.com it's legit. (Even though it's
    # transactional, the brand-impersonation rule shouldn't fire.)
    out = sc.classify(
        sender="PayPal <service@paypal.com>",
        subject="Re: payment",
        snippet="...",
        headers={},
    )
    assert out.cls != "suspicious"


def test_screaming_subject_is_suspicious() -> None:
    out = sc.classify(
        sender="John Smith <john@startup.io>",
        subject="URGENT ACT NOW LIMITED TIME OFFER",
        snippet="claim now",
        headers={},
    )
    assert out.cls == "suspicious"


def test_urgency_spam_phrase_is_suspicious() -> None:
    out = sc.classify(
        sender="x@unknown.io",
        subject="Verify your account today",
        snippet="...",
        headers={},
    )
    assert out.cls == "suspicious"


def test_phishy_snippet_no_display_name_is_suspicious() -> None:
    out = sc.classify(
        sender="x@unknown.io",
        subject="Hi",
        snippet="Click here to verify your account before it is suspended.",
        headers={},
    )
    assert out.cls == "suspicious"


def test_real_email_with_question_mark_is_not_suspicious() -> None:
    # A direct question from a person shouldn't be flagged as urgency-spam.
    out = sc.classify(
        sender="Mary Smith <mary@buyer.co>",
        subject="Quick question about the contract?",
        snippet="Adam, do you have the latest version?",
        headers={},
    )
    assert out.cls == "person"


# --- regression fixtures: real misclassifications found in prod inbox ---


def test_zoom_marketing_via_e_dot_subdomain_is_automated() -> None:
    """Was wrongly suspicious. e.zoom.us is a marketing subdomain; the
    'Don't miss' subject is marketing, not phishing."""
    out = sc.classify(
        sender="Zoom <teamzoom@e.zoom.us>",
        subject="Don't miss summer savings! ⏰",
        snippet="ok",
        headers={},
    )
    assert out.cls == "automated"


def test_linkedin_messages_noreply_is_automated() -> None:
    """Was wrongly person. messages-noreply ends in -noreply suffix → auto."""
    out = sc.classify(
        sender="LinkedIn <messages-noreply@linkedin.com>",
        subject="Marta is popular in your network",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_linkedin_ads_em_subdomain_is_automated() -> None:
    """em.linkedin.com is a marketing subdomain."""
    out = sc.classify(
        sender="LinkedIn Ads <linkedin@em.linkedin.com>",
        subject="Reach verified decision-makers on LinkedIn",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_expedia_eg_subdomain_is_automated() -> None:
    out = sc.classify(
        sender='"Expedia.com" <mail@eg.expedia.com>',
        subject="The secret to earning more OneKeyCash",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_united_enews_subdomain_is_automated() -> None:
    out = sc.classify(
        sender='"United News & Deals" <UnitedAirlines@enews.united.com>',
        subject="Where will you fly next?",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_amazon_store_news_prefix_is_automated() -> None:
    """store-news@ — the store- prefix is now in the automated prefix list."""
    out = sc.classify(
        sender='"Amazon.com" <store-news@amazon.com>',
        subject="Find 4+ star gifts for dads",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_chase_dot_separated_noreply_is_automated() -> None:
    """no.reply.alerts@chase.com — dot-separated local; dots normalize to
    dashes so the -alerts suffix matches."""
    out = sc.classify(
        sender="Chase <no.reply.alerts@chase.com>",
        subject="You received money with Zelle",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_brooksbrothers_offers_subdomain_is_automated() -> None:
    """offers.brooksbrothers.com is a marketing subdomain."""
    out = sc.classify(
        sender="Brooks Brothers <brooksbrothers@offers.brooksbrothers.com>",
        subject="New styles added to sale",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_facebook_notification_priority_is_automated() -> None:
    out = sc.classify(
        sender="Facebook <notification@priority.facebookmail.com>",
        subject="About Nashwa: 1 other new notification",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_tommy_hilfiger_post_subdomain_is_automated() -> None:
    """post.tommy.com is now in the marketing subdomain list."""
    out = sc.classify(
        sender='"Tommy Hilfiger" <info@post.tommy.com>',
        subject="TRENDING NOW",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_screaming_subject_from_personal_address_is_still_suspicious() -> None:
    """If the screaming subject IS from a real-looking personal sender (no
    automated signals), it's still phishing. The reorder didn't disable
    that defense — it just made bulk-mail markers win first."""
    out = sc.classify(
        sender="John Smith <john@startup.io>",
        subject="URGENT ACT NOW LIMITED TIME OFFER",
        snippet="claim now",
        headers={},
    )
    assert out.cls == "suspicious"


# --- v3 fixtures: leaks found in the second prod audit ---


def test_facebookmail_pageupdates_is_automated() -> None:
    """facebookmail.com is on the bulk-domain list (legitimate Facebook mailer)
    so even content-style local parts like pageupdates classify as automated."""
    out = sc.classify(
        sender="Facebook Pages <pageupdates@facebookmail.com>",
        subject="Honor of Kings recently shared a post",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_cinemark_emails_plural_subdomain_is_automated() -> None:
    """emails.cinemark.com (plural) was missed. Now caught."""
    out = sc.classify(
        sender="Cinemark <emails@emails.cinemark.com>",
        subject="See what's New & Now at Cinemark",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_b_subdomain_is_automated() -> None:
    """b.express.com — single-letter ESP throwaway subdomain."""
    out = sc.classify(
        sender="Express <express@b.express.com>",
        subject="Sale is ending! 30% off",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_medallia_feedback_is_automated() -> None:
    """medallia.com is a survey platform — pure bulk mail."""
    out = sc.classify(
        sender="Lexus <Lexus@express.sea1.medallia.com>",
        subject="Tell us about your experience",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_mlb_email_domain_is_automated() -> None:
    """mlbemail.com is on the bulk domain list."""
    out = sc.classify(
        sender="Red Sox <redsox@marketing.mlbemail.com>",
        subject="The Grand Slam Giveaway is LIVE!",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_french_auto_reply_is_automated() -> None:
    """L'Oréal auto-reply in French: 'Réponse automatique : ...'."""
    out = sc.classify(
        sender="AZOUNI Wissal <Wissal.AZOUNI@loreal.com>",
        subject="Réponse automatique : Adam, Bienvenue chez L'Oréal",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_english_auto_reply_is_automated() -> None:
    out = sc.classify(
        sender="Mary Smith <mary@buyer.co>",
        subject="Out of office: back Monday",
        snippet="I'm out until Monday.",
        headers={},
    )
    assert out.cls == "automated"


def test_german_auto_reply_is_automated() -> None:
    out = sc.classify(
        sender="Hans <hans@de.co>",
        subject="Abwesenheitsnotiz: nicht im Büro",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


def test_spanish_auto_reply_is_automated() -> None:
    out = sc.classify(
        sender="Maria <maria@es.co>",
        subject="Respuesta automática: estoy fuera",
        snippet="...",
        headers={},
    )
    assert out.cls == "automated"


# --- user overrides ---


def test_vip_override_promotes_a_marketer(user: User) -> None:
    user.preferences = {"sender_overrides": {"vip": ["board@brand.co"]}}
    out = sc.classify(
        sender="board@brand.co",
        subject="Your weekly digest",
        snippet="...",
        headers={"list-unsubscribe": "<https://x>"},
        user=user,
    )
    # Even though headers say bulk, the VIP override wins.
    assert out.cls == "vip"


def test_muted_override_buries_a_person(user: User) -> None:
    user.preferences = {"sender_overrides": {"muted": ["noisy@person.co"]}}
    out = sc.classify(
        sender="Noisy <noisy@person.co>",
        subject="Sign the contract",
        snippet="Hi adam",
        headers={},
        user=user,
    )
    assert out.cls == "muted"


def test_domain_only_vip_override(user: User) -> None:
    # Bare domain in the override → matches everyone at that domain.
    user.preferences = {"sender_overrides": {"vip": ["board.co"]}}
    out = sc.classify(
        sender="anyone@board.co",
        subject="hi",
        snippet="ok",
        headers={},
        user=user,
    )
    assert out.cls == "vip"


def test_subdomain_matches_domain_override(user: User) -> None:
    user.preferences = {"sender_overrides": {"muted": ["news.io"]}}
    out = sc.classify(
        sender="alerts@daily.news.io",
        subject="hi",
        snippet="ok",
        headers={},
        user=user,
    )
    assert out.cls == "muted"


# --- helpers ---


def test_screaming_detects_all_caps() -> None:
    assert sc._is_screaming("URGENT ACT NOW LIMITED")
    assert not sc._is_screaming("Re: URGENT ACT NOW")  # Re prefix excluded
    assert not sc._is_screaming("Quick question")  # mixed case


def test_phishy_snippet_detection() -> None:
    assert sc._is_phishy_snippet("click here to verify your account")
    assert sc._is_phishy_snippet("Your account has been suspended")
    assert not sc._is_phishy_snippet("can you confirm Friday?")  # genuine ask


def test_impersonation_detection() -> None:
    assert sc._impersonated_brand("PayPal", "paypa1.scam.tk") == "paypal"
    assert sc._impersonated_brand("PayPal Inc", "paypal.com") is None
    assert sc._impersonated_brand("PayPal Inc", "support.paypal.com") is None
    assert sc._impersonated_brand("Mary Smith", "buyer.co") is None
