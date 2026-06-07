"""Enums shared across models and schemas. Mirror packages/shared-types/src/enums.ts."""

import enum


class Provider(enum.StrEnum):
    google = "google"
    notion = "notion"
    todoist = "todoist"
    slack = "slack"


class SyncStatus(enum.StrEnum):
    never = "never"
    syncing = "syncing"
    ok = "ok"
    error = "error"


class MessageClassification(enum.StrEnum):
    needs_reply = "needs_reply"
    needs_decision = "needs_decision"
    deadline = "deadline"
    meeting_scheduling = "meeting_scheduling"
    follow_up_needed = "follow_up_needed"
    waiting_for_response = "waiting_for_response"
    informational = "informational"
    low_priority = "low_priority"
    spam_noise = "spam_noise"
    sensitive = "sensitive"


class Priority(enum.StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    noise = "noise"


class CommitmentOwner(enum.StrEnum):
    user = "user"  # the user owes someone something
    counterparty = "counterparty"  # someone owes the user


class CommitmentStatus(enum.StrEnum):
    open = "open"
    done = "done"
    snoozed = "snoozed"
    dismissed = "dismissed"


class TaskStatus(enum.StrEnum):
    open = "open"
    done = "done"
    snoozed = "snoozed"


class RelationshipType(enum.StrEnum):
    """Who this person is to the user (PRD 15.1 Person.relationship_type).
    Mostly advisory; the ranker reads `importance_weight`, not this string."""

    unknown = "unknown"
    self_ = "self"  # the user themselves
    colleague = "colleague"  # same email domain as the user
    client = "client"  # high outbound traffic at a non-personal domain
    vendor = "vendor"  # role accounts at vendor domains
    investor = "investor"
    family = "family"  # user-overridable
    friend = "friend"  # user-overridable
    automated = "automated"  # bulk / role / no-reply senders
    suspicious = "suspicious"  # phishing / impersonation


class ProjectStatus(enum.StrEnum):
    active = "active"
    on_hold = "on_hold"
    done = "done"
    archived = "archived"


class SourceType(enum.StrEnum):
    gmail = "gmail"
    calendar = "calendar"
    manual = "manual"
    voice = "voice"


# Action risk levels per PRD section 12.10. Levels 4-5 require strong confirmation.
class RiskLevel(enum.IntEnum):
    read_only = 0
    internal_prep = 1
    reversible_write = 2
    external_comm = 3
    financial_legal = 4
    sensitive = 5


class ActionType(enum.StrEnum):
    create_draft = "create_draft"  # push a reply into Gmail drafts (level 3)
    create_task = "create_task"  # level 2 reversible write
    create_calendar_event = "create_calendar_event"  # level 2: book your own time
    send_email = "send_email"  # level 3 external comm
    send_message = "send_message"  # level 3 (e.g. WhatsApp)
    make_payment = "make_payment"  # level 4 financial
    place_order = "place_order"  # level 4 financial (commerce)
    create_notion_page = "create_notion_page"  # level 2 reversible write
    create_todoist_task = "create_todoist_task"  # level 2 reversible write
    send_slack_message = "send_slack_message"  # level 3 external comm
    browser_action = "browser_action"  # refused; see docs/integrations/REFUSED.md


class ActionStatus(enum.StrEnum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    executed = "executed"
    failed = "failed"


class NotificationType(enum.StrEnum):
    deadline_risk = "deadline_risk"
    meeting_prep = "meeting_prep"
    unanswered_email = "unanswered_email"
    follow_up_due = "follow_up_due"
    daily_briefing = "daily_briefing"
    approval_needed = "approval_needed"
    schedule_conflict = "schedule_conflict"
    reminder = "reminder"


class NotificationStatus(enum.StrEnum):
    pending = "pending"  # queued, not yet sent (e.g. held by quiet hours)
    sent = "sent"
    suppressed = "suppressed"  # batched away or below threshold


# Priority floor a notification type must clear to send immediately vs. batch.
class NotificationImportance(enum.IntEnum):
    low = 1
    normal = 2
    high = 3
