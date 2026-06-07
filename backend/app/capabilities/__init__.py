"""Capability registry. Maps an ActionType to its provider. The execution service
looks providers up here; routes never touch providers directly.

Registering a capability here is the single switch that turns it on. Refused
capabilities (browser, delivery) are registered to providers that raise with a
documented reason rather than being absent, so the seam is explicit."""

from functools import lru_cache

from app.capabilities.base import CapabilityProvider
from app.db.enums import ActionType


@lru_cache
def _registry() -> dict[ActionType, CapabilityProvider]:
    from app.capabilities.providers.browser_action import BrowserActionCapability
    from app.capabilities.providers.calendar_event import CalendarEventCapability
    from app.capabilities.providers.create_task import CreateTaskCapability
    from app.capabilities.providers.delivery_order import DeliveryOrderCapability
    from app.capabilities.providers.gmail_draft import GmailDraftCapability
    from app.capabilities.providers.notion_page import NotionPageCapability
    from app.capabilities.providers.send_email import SendEmailCapability
    from app.capabilities.providers.slack_message import SlackMessageCapability
    from app.capabilities.providers.todoist_task import TodoistTaskCapability
    from app.core.config import get_settings

    providers: list[CapabilityProvider] = [
        GmailDraftCapability(),
        SendEmailCapability(),
        CreateTaskCapability(),
        CalendarEventCapability(),
        # Phase 2 integrations. The capability is always registered; the
        # ConnectedAccount lookup inside .execute is what gates them per-user.
        # When no account is connected, execute raises a clear CapabilityError
        # and the action falls back to the manual approval queue.
        NotionPageCapability(),
        TodoistTaskCapability(),
        SlackMessageCapability(),
        # Refused capabilities are always registered so the boundary is explicit:
        # they raise a sourced CapabilityError. See docs/integrations/REFUSED.md.
        BrowserActionCapability(),
        DeliveryOrderCapability(),
    ]

    settings = get_settings()
    # Payments register only when a Stripe key is present, so make_payment stays
    # absent (and blocks) on an unconfigured deployment.
    if settings.stripe_secret_key:
        from app.capabilities.providers.stripe_payment import StripePaymentCapability

        providers.append(StripePaymentCapability())

    # WhatsApp registers only when the Cloud API is configured.
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        from app.capabilities.providers.whatsapp_message import WhatsAppMessageCapability

        providers.append(WhatsAppMessageCapability())

    return {p.describe().action_type: p for p in providers}


def get_capability(action_type: ActionType) -> CapabilityProvider | None:
    return _registry().get(action_type)


def register(provider: CapabilityProvider) -> None:
    """Register a provider at runtime (used by B3/B4 to add Stripe/WhatsApp)."""
    _registry()[provider.describe().action_type] = provider
