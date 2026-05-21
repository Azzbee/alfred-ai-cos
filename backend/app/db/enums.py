"""Enums shared across models and schemas. Mirror packages/shared-types/src/enums.ts."""

import enum


class Provider(enum.StrEnum):
    google = "google"


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


class SourceType(enum.StrEnum):
    gmail = "gmail"
    calendar = "calendar"
    manual = "manual"
    voice = "voice"


# Action risk levels per PRD section 12.10. The slice only uses up to level 3 (send email),
# which is the boundary the approval system must guard.
class RiskLevel(enum.IntEnum):
    read_only = 0
    internal_prep = 1
    reversible_write = 2
    external_comm = 3
    financial_legal = 4
    sensitive = 5


class ActionType(enum.StrEnum):
    send_email = "send_email"  # level 3, requires approval
    create_draft = "create_draft"  # level 1
    create_task = "create_task"  # level 2


class ActionStatus(enum.StrEnum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    executed = "executed"
    failed = "failed"
