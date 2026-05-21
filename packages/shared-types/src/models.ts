// DTOs mirrored from backend/app/schemas. These are the wire shapes the API returns.

import type {
  ActionStatus,
  CommitmentOwner,
  CommitmentStatus,
  Priority,
  SourceType,
  TaskStatus,
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

export interface UpcomingMeeting {
  id: string;
  title: string | null;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  attendees: string[];
  prep_required: boolean;
}

export interface MeetingPrep {
  event: UpcomingMeeting;
  summary: string;
  open_commitments: string[];
  suggested_questions: string[];
  related_message_count: number;
}

export interface Briefing {
  id: string;
  date: string;
  summary: string;
  user_feedback: string | null;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  priority: Priority;
  status: TaskStatus;
  source_type: SourceType;
  source_id: string | null;
}

export interface TaskCreateRequest {
  title: string;
  description?: string | null;
  due_date?: string | null;
  priority?: Priority;
}

export interface CaptureResponse {
  tasks: Task[];
  detected_project: string | null;
}

export interface WaitingEntry {
  id: string;
  description: string;
  counterparty: string | null;
  due_date: string | null;
  age_days: number;
  source_type: SourceType;
  source_id: string | null;
}

export interface WaitingView {
  waiting_on_you: WaitingEntry[];
  you_are_waiting_on: WaitingEntry[];
}

export interface OnboardingPrefs {
  focus?: string | null;
  optimize_for?: string | null;
  proactiveness?: string | null;
}

export interface Me {
  id: string;
  email: string;
  name: string | null;
  timezone: string;
  preferences: Record<string, unknown>;
  onboarded: boolean;
}

export interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string;
  status: string;
  useful: boolean | null;
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
