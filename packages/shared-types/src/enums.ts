// Mirrors backend/app/db/enums.py. Keep the two in sync when either changes.

export const Priority = {
  Critical: "critical",
  High: "high",
  Medium: "medium",
  Low: "low",
  Noise: "noise",
} as const;
export type Priority = (typeof Priority)[keyof typeof Priority];

export const CommitmentOwner = {
  User: "user",
  Counterparty: "counterparty",
} as const;
export type CommitmentOwner = (typeof CommitmentOwner)[keyof typeof CommitmentOwner];

export const CommitmentStatus = {
  Open: "open",
  Done: "done",
  Snoozed: "snoozed",
  Dismissed: "dismissed",
} as const;
export type CommitmentStatus = (typeof CommitmentStatus)[keyof typeof CommitmentStatus];

export const MessageClassification = {
  NeedsReply: "needs_reply",
  NeedsDecision: "needs_decision",
  Deadline: "deadline",
  MeetingScheduling: "meeting_scheduling",
  FollowUpNeeded: "follow_up_needed",
  WaitingForResponse: "waiting_for_response",
  Informational: "informational",
  LowPriority: "low_priority",
  SpamNoise: "spam_noise",
  Sensitive: "sensitive",
} as const;
export type MessageClassification =
  (typeof MessageClassification)[keyof typeof MessageClassification];

export const ActionStatus = {
  Proposed: "proposed",
  Approved: "approved",
  Rejected: "rejected",
  Executed: "executed",
  Failed: "failed",
} as const;
export type ActionStatus = (typeof ActionStatus)[keyof typeof ActionStatus];

// Action risk levels (PRD 12.10). The slice guards the level-3 boundary.
export const RiskLevel = {
  ReadOnly: 0,
  InternalPrep: 1,
  ReversibleWrite: 2,
  ExternalComm: 3,
  FinancialLegal: 4,
  Sensitive: 5,
} as const;
export type RiskLevel = (typeof RiskLevel)[keyof typeof RiskLevel];
