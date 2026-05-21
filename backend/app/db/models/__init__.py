"""ORM models for Albert's first vertical slice.

Only the entities on the path Gmail OAuth -> ingestion -> commitment extraction ->
Today priorities -> draft reply are modeled here, plus the ownership (User,
ConnectedAccount) and approval/audit spine (ActionProposal, ExecutionLog).

Entities from the PRD data model not yet needed by the slice (Person, Project,
DailyBriefing) are intentionally deferred. See docs/ARCHITECTURE.md.
"""

from app.db.models.action import ActionProposal, ExecutionLog
from app.db.models.calendar_event import CalendarEvent
from app.db.models.commitment import Commitment
from app.db.models.connected_account import ConnectedAccount
from app.db.models.draft_reply import DraftReply
from app.db.models.message import Message
from app.db.models.task import Task
from app.db.models.user import User

__all__ = [
    "ActionProposal",
    "CalendarEvent",
    "Commitment",
    "ConnectedAccount",
    "DraftReply",
    "ExecutionLog",
    "Message",
    "Task",
    "User",
]
