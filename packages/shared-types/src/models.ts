// DTOs mirrored from backend/app/schemas. These are the wire shapes the API returns.

import type {
  ActionStatus,
  CommitmentOwner,
  CommitmentStatus,
  Priority,
} from "./enums.js";

export interface TodayPriority {
  id: string;
  title: string;
  priority: Priority;
  reason: string;
  due_date: string | null; // ISO date
  counterparty: string | null;
  confidence: number;
}

export interface WaitingItem {
  id: string;
  description: string;
  person: string | null;
}

export interface MeetingToPrepare {
  id: string;
  title: string | null;
  start_time: string | null;
}

export interface TodayDashboard {
  summary: string;
  top_priorities: TodayPriority[];
  people_waiting_on_you: WaitingItem[];
  you_are_waiting_on: WaitingItem[];
  meetings_to_prepare: MeetingToPrepare[];
}

export interface Commitment {
  id: string;
  description: string;
  owner: CommitmentOwner;
  counterparty: string | null;
  due_date: string | null;
  priority: Priority;
  status: CommitmentStatus;
  evidence: string | null;
  confidence: number;
}

export interface Draft {
  id: string;
  message_id: string;
  subject: string | null;
  body: string;
  tone: string;
  gmail_draft_id: string | null;
}

export interface DraftCreateRequest {
  message_id: string;
  tone?: string;
  instruction?: string | null;
}

export interface ActionProposal {
  id: string;
  action_type: string;
  risk_level: number;
  reason: string | null;
  status: ActionStatus;
}

export interface SyncResponse {
  ingested: number;
  commitments_found: number;
}

export interface SessionToken {
  access_token: string;
  token_type: string;
}

export interface AuthStartResponse {
  authorization_url: string;
  state: string;
}
