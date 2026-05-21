"""ORM models for Albert.

Covers ownership (User, ConnectedAccount), the ingestion/extraction path (Message,
CalendarEvent, Commitment, Task, DraftReply), daily briefings, and the approval/
audit spine (ActionProposal, ExecutionLog).

PRD entities not yet needed (Person, Project) are deferred. See docs/ARCHITECTURE.md.
"""

from app.db.models.action import ActionProposal, ExecutionLog
from app.db.models.briefing import DailyBriefing
from app.db.models.calendar_event import CalendarEvent
from app.db.models.commitment import Commitment
from app.db.models.connected_account import ConnectedAccount
from app.db.models.draft_reply import DraftReply
from app.db.models.message import Message
from app.db.models.notification import Device, Notification
from app.db.models.task import Task
from app.db.models.user import User

__all__ = [
    "ActionProposal",
    "CalendarEvent",
    "Commitment",
    "ConnectedAccount",
    "DailyBriefing",
    "Device",
    "DraftReply",
    "ExecutionLog",
    "Message",
    "Notification",
    "Task",
    "User",
]
