# Product Requirements Document — Albert

## Product Name

**Albert**

## Working Tagline

**Albert keeps you above your priorities.**

Alternative positioning lines:

- **Your AI Chief of Staff for life and work.**
- **The execution layer for your personal life.**
- **Albert finds what you are forgetting and helps you get it done.**
- **Turn your inbox, calendar, and thoughts into a clear plan.**

---

# 1. Executive Summary

Albert is a mobile-first AI assistant that helps users stay on top of everything on their plate by continuously transforming scattered information from email, calendar, voice notes, tasks, documents, and messages into clear priorities, reminders, drafts, and executable next actions.

Albert is not a generic chatbot and not simply another to-do list. Its core purpose is to reduce the number of open loops in a user’s life.

An open loop is anything the user has to remember, respond to, prepare, decide, send, schedule, follow up on, or act upon.

Albert’s first product wedge is simple:

> **Connect Gmail and Google Calendar. Albert finds what matters, what you are forgetting, who is waiting on you, and what you should do next.**

The product starts as a personal priority and execution assistant. Over time, Albert evolves into an AI chief of staff that can help users plan, draft, schedule, follow up, prepare for meetings, manage commitments, coordinate across apps, and eventually perform approved actions such as bookings, purchases, and service orders.

---

# 2. Product Vision

## 2.1 Vision Statement

Albert becomes the trusted AI layer between a person and their responsibilities.

It understands what is happening across their life, identifies what matters, recommends what to do next, and helps them execute safely with user approval.

## 2.2 Long-Term Ambition

Albert should become the default personal operating system for busy people.

It should answer questions like:

- What am I forgetting?
- What should I do first?
- Who is waiting for me?
- What is becoming urgent?
- What needs my approval?
- What should I prepare before my next meeting?
- What can you draft for me?
- What can you handle for me?

The long-term goal is for Albert to become a trusted daily companion that reduces stress, increases execution quality, and gives users the feeling that their life is under control.

---

# 3. Problem Statement

Modern users do not suffer from a lack of productivity tools. They suffer from fragmentation, overload, and invisible obligations.

Their responsibilities are spread across:

- email;
- calendar;
- WhatsApp;
- Slack;
- notes;
- documents;
- voice notes;
- screenshots;
- task apps;
- school or work platforms;
- personal conversations;
- meetings;
- mental reminders.

Existing tools force users to manually capture, organize, prioritize, and execute everything. Most users fail at this because the system depends on them being perfectly organized.

Albert solves this by becoming proactive.

Instead of asking the user to maintain a perfect task system, Albert watches the user’s approved information sources, extracts commitments, ranks priorities, drafts next actions, and reminds the user when something is at risk of being missed.

## 3.1 Core User Pain Points

### Pain Point 1 — Scattered obligations

Users receive requests through many channels and forget where things were mentioned.

Example:

> “Someone asked me to send a document, but I cannot remember if it was by email, WhatsApp, or during a call.”

### Pain Point 2 — Unclear priorities

Users have many things to do, but do not know what actually matters today.

Example:

> “I have 30 things on my mind, but I do not know which 3 are actually urgent.”

### Pain Point 3 — Missed follow-ups

Users forget to follow up with people, respond to important emails, or chase pending items.

Example:

> “I said I would send this yesterday and completely forgot.”

### Pain Point 4 — Calendar without preparation

Users attend meetings without remembering the context, previous discussion, or required preparation.

Example:

> “I have a call in 20 minutes but I forgot what we discussed last time.”

### Pain Point 5 — To-do lists are passive

Traditional task apps only help if the user manually creates and maintains tasks. They do not infer tasks automatically from communication.

### Pain Point 6 — Mental load

Users carry too many open loops in their head, creating stress and a constant feeling of falling behind.

---

# 4. Product Thesis

Albert wins if it becomes the user’s trusted daily control center.

The product thesis is:

> Users do not want another AI chatbot. They want an assistant that knows what is on their plate, tells them what matters, and helps them act.

Therefore, Albert must be:

1. **Context-aware** — connected to the user’s real sources of responsibility.
2. **Proactive** — surfaces important items before the user asks.
3. **Action-oriented** — drafts, schedules, reminds, and prepares.
4. **Trustworthy** — never sends, buys, cancels, signs, or pays without appropriate approval.
5. **Explainable** — tells the user why something is important.
6. **Mobile-first** — designed for quick capture, review, approval, and action.

---

# 5. Target Users

## 5.1 Initial Ideal Customer Profile

Albert should initially target ambitious, overloaded users whose responsibilities are heavily communication-driven.

### Primary ICP 1 — Founders and startup operators

They live in email, calendar, WhatsApp, investor updates, hiring messages, customer calls, and documents.

Key needs:

- track investor/customer follow-ups;
- prepare for meetings;
- manage urgent emails;
- keep fundraising, product, hiring, and operations moving;
- avoid dropping important relationships.

Why they are ideal:

- high pain;
- high willingness to pay;
- high tolerance for early product imperfections if value is strong;
- frequent usage;
- strong word of mouth.

### Primary ICP 2 — Ambitious students and young professionals

Especially students managing school, internships, applications, associations, side projects, and personal admin.

Key needs:

- organize deadlines;
- track applications;
- prepare emails;
- manage school/project commitments;
- reduce stress;
- create daily plans.

Why they are ideal:

- strong daily pain;
- willing to test new tools;
- good viral potential;
- strong use case for mobile-first experience.

### Primary ICP 3 — Executives, family office members, and business owners

They handle many relationships, deals, meetings, documents, and follow-ups.

Key needs:

- know who is waiting;
- prepare for calls;
- track deal/admin commitments;
- draft professional messages;
- avoid missing high-stakes items.

Why they are ideal:

- high willingness to pay;
- clear ROI;
- high cost of missed follow-ups.

## 5.2 Later ICPs

- lawyers;
- consultants;
- bankers;
- real estate brokers;
- medical professionals;
- sales teams;
- recruiters;
- personal assistants;
- small business owners.

---

# 6. Core Product Promise

Albert’s core promise is:

> **Every morning, Albert tells you what matters. During the day, Albert catches what you might miss. When action is needed, Albert helps you execute.**

This promise breaks down into five capabilities:

1. **Find** what matters.
2. **Explain** why it matters.
3. **Prioritize** what should happen next.
4. **Prepare** the action.
5. **Follow up** until the loop is closed.

---

# 7. MVP Scope

## 7.1 MVP Objective

The MVP should prove that Albert can create a meaningful daily control center from a user’s Gmail and Google Calendar.

The MVP should answer:

> Can Albert reliably identify important obligations and help the user take action?

## 7.2 MVP Integrations

### Required for MVP

- Gmail
- Google Calendar
- Manual task creation
- Voice/text capture
- Push notifications

### Optional for MVP

- Notion
- Todoist
- Slack
- Google Drive

### Explicitly out of MVP

- autonomous purchases;
- Uber Eats / Deliveroo ordering;
- banking actions;
- WhatsApp automation;
- full browser automation;
- legal document signing;
- multi-user team workspace;
- full enterprise admin console.

## 7.3 MVP Product Capabilities

The MVP must include:

1. Account creation and onboarding.
2. Gmail and Calendar connection.
3. Email ingestion and classification.
4. Calendar ingestion.
5. Action item extraction.
6. Commitment detection.
7. Priority scoring.
8. Today dashboard.
9. Daily briefing.
10. Meeting preparation.
11. Draft email replies.
12. Create tasks.
13. Create calendar events.
14. Smart reminders.
15. Approval flow for external actions.
16. User feedback loop.

---

# 8. Product Principles

## Principle 1 — Today is the homepage

Albert should not open to a blank chat screen.

The primary screen should be **Today**, showing what matters now.

## Principle 2 — Action beats information

Albert should avoid giving long summaries unless needed. The default output should be a next action.

Poor output:

> “You have many emails related to Barnes.”

Good output:

> “You need to send financial clarification questions to Chaker today. I drafted them.”

## Principle 3 — Explain priority

Albert should never simply say “high priority.” It should explain why.

Example:

> “High priority because the deadline is tomorrow, Chaker is waiting, and this blocks the acquisition review.”

## Principle 4 — User remains in control

Albert can prepare actions, but should not perform sensitive or external actions without approval.

## Principle 5 — Reduce open loops

Every feature must help close, clarify, defer, delegate, or remove an open loop.

## Principle 6 — Be calm, not noisy

Albert should not spam the user with notifications. It should surface fewer, better alerts.

## Principle 7 — Trust is the product

The user must feel that Albert is accurate, private, explainable, and safe.

---

# 9. User Experience Overview

## 9.1 First-Time Onboarding

### Goal

Help the user experience value within the first 5 minutes.

### Flow

1. User downloads Albert.
2. User creates account.
3. Albert explains the value in one sentence:

   > “Connect Gmail and Calendar. I will find what matters, what you are forgetting, and what needs action.”

4. User connects Gmail.
5. User connects Google Calendar.
6. Albert asks 3 calibration questions:

   - What do you mainly want help with?
     - Work
     - School
     - Personal admin
     - Founder/startup
     - All of the above

   - What should Albert optimize for?
     - Never miss deadlines
     - Clear daily priorities
     - Better follow-ups
     - Meeting preparation
     - Inbox control

   - How proactive should Albert be?
     - Quiet
     - Balanced
     - Very proactive

7. Albert scans recent email/calendar data.
8. Albert generates the first “What you may be forgetting” report.
9. User confirms or rejects suggested items.
10. Albert creates the first Today dashboard.

### First Magic Moment

Within onboarding, Albert should say something like:

> “I found 6 things that may require your attention. 2 look urgent, 3 are waiting for your reply, and 1 relates to tomorrow’s meeting.”

This is the moment that proves the product.

---

# 10. Core Screens

## 10.1 Today Screen

The Today screen is Albert’s main interface.

### Purpose

Give the user a calm, clear view of what matters now.

### Required Sections

#### 1. Daily Summary

Example:

> “You have 12 open loops. 3 matter today. 2 people are waiting for you. Your next meeting needs preparation.”

#### 2. Top Priorities

Each priority card includes:

- title;
- reason;
- deadline;
- related person/project;
- suggested action;
- button to act.

Example card:

**Send Barnes financial clarification questions**  
Due today · High priority  
Reason: Chaker is waiting, and this blocks the financial review.  
Suggested action: Review prepared draft.

Buttons:

- Review Draft
- Snooze
- Mark Done
- Not Important

#### 3. People Waiting on You

Shows emails/messages where someone expects a response.

#### 4. You Are Waiting On

Shows open loops where the user is waiting for someone else.

#### 5. Meetings to Prepare

Shows upcoming calendar events requiring preparation.

#### 6. Quick Wins

Small tasks that take less than 5 minutes.

#### 7. Albert Suggestions

Proactive recommendations:

- “You have 45 minutes before your next meeting. Best use: finish the Barnes draft.”
- “You did not reply to this email for 5 days. Want me to draft a follow-up?”

---

## 10.2 Ask Albert Screen

### Purpose

Let the user ask natural-language questions about their responsibilities.

### Example Queries

- What am I forgetting?
- What should I do first?
- Who is waiting for me?
- What is urgent today?
- Prepare me for my next meeting.
- Draft replies to my important emails.
- What is blocking project X?
- What did I promise Chaker?
- What do I need to do before Friday?

### Expected Behavior

Albert should answer with structured outputs and action buttons.

Poor answer:

> “You have several tasks.”

Good answer:

> “The most important thing is sending the financial clarification questions to Chaker. It is due today, and it blocks the Barnes acquisition review. I prepared a draft.”

Buttons:

- Review Draft
- Add to Today
- Snooze
- Mark Done

---

## 10.3 Capture Screen

### Purpose

Allow fast manual capture by voice or text.

### Example Input

> “Albert, tomorrow remind me to call the broker, review the CBRE valuation, and send the pellet line offer in French.”

### Albert Output

Creates:

1. Task: Call the broker tomorrow.
2. Task: Review the CBRE valuation.
3. Task: Draft French pellet line offer.
4. Project: Factory Sale, if detected.
5. Suggested reminder: tomorrow morning.

### Capture Types

- voice note;
- typed note;
- forwarded text;
- screenshot upload;
- copied email/message;
- document summary later.

---

## 10.4 Priority Inbox

### Purpose

Separate important/actionable messages from noise.

### Categories

- Needs Reply
- Needs Decision
- Deadline
- Waiting For You
- FYI
- Low Priority
- Potentially Important

### Message Card Fields

- sender;
- subject;
- summary;
- required action;
- deadline;
- priority;
- confidence;
- suggested reply;
- evidence.

---

## 10.5 Meeting Prep Screen

### Purpose

Prepare the user before calls and meetings.

### Trigger

Upcoming calendar event within configurable window, e.g. 30–60 minutes before.

### Meeting Brief Includes

- meeting title;
- attendees;
- relevant previous emails;
- open commitments;
- questions to ask;
- documents to review;
- suggested agenda;
- last interaction summary;
- risks or unresolved issues.

### Example

**Meeting with Celine — 14:00**

Context:

- Last discussed lunch invitation timing.
- Potential scheduling conflict detected.
- No reply sent yet.

Suggested prep:

1. Confirm timing.
2. Clarify location.
3. Check calendar conflict.

Button:

- Draft Confirmation Reply

---

## 10.6 Action Approval Screen

### Purpose

Allow user to safely approve external actions.

### Approval Card Includes

- action type;
- recipient/platform;
- exact content/action;
- consequences;
- reversibility;
- confidence;
- approval buttons.

Example:

**Ready to send email to Chaker**

Subject: Barnes Financial Clarification Questions

Albert will send this email from your Gmail account.

Buttons:

- Send
- Edit
- Save as Draft
- Cancel

---

# 11. Core User Journeys

## Journey 1 — Morning Priority Briefing

### User Story

As a busy user, I want Albert to tell me what matters today so I can start the day with clarity.

### Flow

1. User opens Albert in the morning.
2. Albert displays Today dashboard.
3. User sees top 3 priorities.
4. Albert explains why each matters.
5. User accepts the proposed plan.
6. User reviews drafts or schedules time blocks.

### Success Criteria

- User understands their day within 60 seconds.
- User accepts or acts on at least one suggested priority.
- User feels Albert surfaced something useful.

---

## Journey 2 — Forgotten Commitment Detection

### User Story

As a user, I want Albert to catch things I promised so I do not forget them.

### Flow

1. Albert ingests emails.
2. Albert detects phrase: “I’ll send this tomorrow.”
3. Albert creates a commitment object.
4. Albert assigns due date.
5. Albert surfaces it before risk threshold.
6. User marks done, snoozes, or asks Albert to draft.

### Success Criteria

- Albert detects commitments with high precision.
- User confirms the item is real.
- User completes or schedules the task.

---

## Journey 3 — Email Reply Drafting

### User Story

As a user, I want Albert to draft replies to important emails so I can respond faster.

### Flow

1. Albert identifies email requiring reply.
2. Albert summarizes request.
3. Albert proposes reply.
4. User reviews.
5. User edits or approves.
6. Albert creates Gmail draft or sends with confirmation.

### Success Criteria

- Draft is contextually correct.
- Draft matches user tone.
- User approves or edits lightly.

---

## Journey 4 — Meeting Preparation

### User Story

As a user, I want Albert to prepare me before meetings so I know the context and next steps.

### Flow

1. Albert detects upcoming meeting.
2. Albert retrieves related email threads and calendar history.
3. Albert generates meeting brief.
4. User reviews brief.
5. Albert suggests questions and follow-up items.

### Success Criteria

- User opens meeting brief.
- Brief contains relevant context.
- User feels more prepared.

---

## Journey 5 — Waiting-For Follow-Up

### User Story

As a user, I want Albert to remind me when someone has not responded to something important.

### Flow

1. Albert detects user sent a request.
2. No reply received after expected timeframe.
3. Albert surfaces “waiting on” item.
4. User asks Albert to draft follow-up.
5. User approves draft.

### Success Criteria

- Follow-up is timely.
- User finds reminder useful.
- User sends or schedules follow-up.

---

## Journey 6 — Voice Capture to Plan

### User Story

As a user, I want to quickly dump thoughts into Albert and have them structured into tasks.

### Flow

1. User taps microphone.
2. User speaks messy instructions.
3. Albert transcribes.
4. Albert extracts tasks, dates, people, and projects.
5. User confirms.
6. Albert updates Today or project plan.

### Success Criteria

- Captured note is accurately structured.
- User can confirm in less than 30 seconds.

---

# 12. Functional Requirements

## 12.1 Authentication and Account Management

### Requirements

- User can create account using email/password or OAuth.
- User can connect and disconnect integrations.
- User can delete account and associated data.
- User can manage notification preferences.
- User can manage approval policies.

### Acceptance Criteria

- User can sign up and reach onboarding.
- User can revoke Gmail/Calendar access.
- User can request data deletion.

---

## 12.2 Gmail Integration

### Requirements

Albert must be able to:

- connect to Gmail through OAuth;
- ingest email metadata and body content according to granted permissions;
- classify emails;
- detect action items;
- detect deadlines;
- detect reply requirements;
- identify important senders;
- create Gmail drafts;
- send email only after explicit approval.

### Email Classification Categories

- Needs Reply
- Needs Decision
- Deadline
- Meeting Scheduling
- Follow-Up Needed
- Waiting For Response
- Informational
- Low Priority
- Spam/Noise
- Sensitive

### Acceptance Criteria

- Albert can classify recent emails into categories.
- Albert can create an accurate draft reply.
- Albert does not send without approval.

---

## 12.3 Calendar Integration

### Requirements

Albert must be able to:

- connect to Google Calendar;
- read upcoming events;
- identify meetings requiring prep;
- identify free time blocks;
- propose time blocks for priorities;
- create calendar events after user approval;
- detect conflicts.

### Acceptance Criteria

- Albert shows upcoming meetings.
- Albert generates meeting prep for relevant events.
- Albert can propose a realistic daily plan using free time.

---

## 12.4 Task Management

### Requirements

Albert must allow users to:

- create tasks manually;
- create tasks from email;
- create tasks from voice capture;
- mark tasks complete;
- snooze tasks;
- assign due dates;
- assign projects;
- assign priority;
- link tasks to source evidence.

### Acceptance Criteria

- Every extracted task has a source or user-created origin.
- User can correct task title, deadline, and priority.
- Albert learns from corrections.

---

## 12.5 Commitment Detection

### Requirements

Albert must detect commitments from text.

Commitment types:

- user owes someone something;
- someone owes the user something;
- user promised to follow up;
- user needs to decide;
- user needs to prepare;
- user needs to attend;
- user needs to send/sign/pay/review something.

### Commitment Object

A commitment must include:

- description;
- owner;
- counterparty;
- due date if available;
- source;
- evidence quote;
- confidence;
- priority;
- status.

### Acceptance Criteria

- Albert can distinguish between “I need to do this” and “someone else needs to do this.”
- Albert does not create high-risk commitments without sufficient confidence.
- Low-confidence commitments are shown as suggestions, not facts.

---

## 12.6 Priority Engine

### Requirements

Albert must rank tasks and commitments using a hybrid model.

Factors:

- urgency;
- importance;
- deadline proximity;
- relationship importance;
- financial/legal/professional consequence;
- user-stated goals;
- project relevance;
- effort required;
- dependency/blocker status;
- previous user behavior;
- explicit user overrides.

### Priority Levels

- Critical
- High
- Medium
- Low
- Ignored/Noise

### Explanation Requirement

Every priority recommendation must include a human-readable reason.

Example:

> “High priority because it is due tomorrow, the sender is waiting for you, and it blocks the Barnes review.”

### Acceptance Criteria

- User can see why an item is ranked highly.
- User can correct priority.
- Albert incorporates feedback over time.

---

## 12.7 Daily Briefing

### Requirements

Albert must generate a daily briefing at a user-defined time.

Briefing includes:

- top 3–5 priorities;
- overdue items;
- people waiting on user;
- user waiting on others;
- upcoming meetings;
- suggested time blocks;
- quick wins;
- risks.

### Acceptance Criteria

- Briefing is generated reliably.
- Briefing contains no more than 5 primary priorities.
- Briefing is short enough to read in under 90 seconds.

---

## 12.8 Smart Notifications

### Requirements

Albert must notify users only when useful.

Notification types:

- deadline risk;
- meeting prep;
- important unanswered email;
- follow-up due;
- daily briefing;
- approval needed;
- schedule conflict;
- user-defined reminder.

### Notification Principles

- Do not notify for every task.
- Batch low-priority items.
- Escalate only when risk increases.
- Respect quiet hours.

### Acceptance Criteria

- User can configure notification style.
- User can mark notifications as useful/not useful.
- Albert reduces notification noise over time.

---

## 12.9 Drafting and Writing

### Requirements

Albert must draft:

- email replies;
- follow-up emails;
- meeting agendas;
- WhatsApp-style short messages;
- professional notes;
- task summaries;
- reminders.

### Draft Quality Requirements

Drafts must be:

- contextually accurate;
- concise by default;
- tone-matched to user preference;
- editable;
- not sent without approval.

### Acceptance Criteria

- User can edit draft before sending.
- User can regenerate draft.
- User can choose tone: concise, warm, formal, direct.

---

## 12.10 Approval System

### Requirements

Albert must classify actions by risk and require approval accordingly.

### Action Risk Levels

#### Level 0 — Read-only

Examples:

- summarize email;
- analyze calendar;
- answer question.

Approval required: No.

#### Level 1 — Internal preparation

Examples:

- create draft;
- create suggested task;
- prepare order basket conceptually.

Approval required: No or light approval.

#### Level 2 — Reversible internal write

Examples:

- create task;
- create calendar event;
- update project note.

Approval required: configurable.

#### Level 3 — External communication

Examples:

- send email;
- message someone;
- invite attendee.

Approval required: Yes.

#### Level 4 — Financial / legal / irreversible action

Examples:

- place order;
- make payment;
- sign document;
- cancel booking;
- submit official form.

Approval required: Strong confirmation.

#### Level 5 — Sensitive action

Examples:

- medical, legal, financial, employment, or high-stakes decisions.

Approval required: Strong confirmation and careful disclaimers.

### Acceptance Criteria

- Albert never performs Level 3+ actions without explicit approval.
- Every performed action is logged.
- User can review execution history.

---

# 13. Non-Functional Requirements

## 13.1 Privacy

Albert must be designed around user trust.

Requirements:

- use OAuth wherever possible;
- do not store raw passwords;
- allow account deletion;
- allow integration revocation;
- minimize data access scopes;
- encrypt tokens;
- encrypt sensitive stored data;
- provide clear privacy settings;
- do not train global models on user data without explicit consent.

## 13.2 Security

Requirements:

- encrypted token storage;
- role-based backend access;
- audit logs;
- rate limits;
- secure secrets management;
- regular security reviews;
- least-privilege data access;
- strict production logging policy.

## 13.3 Reliability

Requirements:

- daily briefing should generate consistently;
- integration failures should be visible and recoverable;
- user should know when data is stale;
- failed actions should not be silently ignored.

## 13.4 Latency

Target response times:

- Today screen load: under 2 seconds after cached data available.
- Ask Albert response: under 8 seconds for normal queries.
- Draft generation: under 10 seconds.
- Background ingestion: near-real-time where possible, otherwise periodic.

## 13.5 Explainability

Albert must explain:

- why something was prioritized;
- where it found the information;
- what action it proposes;
- what will happen if user approves.

## 13.6 Data Freshness

Albert must display whether information is up to date.

Examples:

- “Gmail synced 4 minutes ago.”
- “Calendar synced just now.”
- “Slack not connected.”

---

# 14. AI System Design

## 14.1 Agent Architecture

Albert should be built as a set of specialized agents coordinated by an orchestration layer.

### Agent 1 — Ingestion Agent

Responsibilities:

- retrieve data from integrations;
- normalize emails, calendar events, tasks, and notes;
- deduplicate items;
- identify source metadata.

### Agent 2 — Extraction Agent

Responsibilities:

- extract tasks;
- extract commitments;
- extract deadlines;
- extract people and organizations;
- extract projects;
- identify open loops.

### Agent 3 — Priority Agent

Responsibilities:

- score urgency;
- score importance;
- determine what matters today;
- explain priority;
- incorporate user feedback.

### Agent 4 — Planning Agent

Responsibilities:

- create daily plan;
- suggest time blocks;
- sequence tasks;
- balance urgency and energy;
- identify quick wins.

### Agent 5 — Drafting Agent

Responsibilities:

- draft emails;
- draft messages;
- write follow-ups;
- summarize context;
- adapt tone.

### Agent 6 — Meeting Prep Agent

Responsibilities:

- detect meetings needing preparation;
- retrieve relevant context;
- generate agenda;
- identify open commitments;
- propose talking points.

### Agent 7 — Memory Agent

Responsibilities:

- learn user preferences;
- track important people;
- track projects;
- remember tone preferences;
- update personal context with explicit or inferred consent rules.

### Agent 8 — Execution Agent

Responsibilities:

- create tasks;
- create drafts;
- create calendar events;
- execute approved actions;
- log actions.

### Agent 9 — Safety and Approval Agent

Responsibilities:

- classify action risk;
- enforce approval policies;
- block unsafe actions;
- explain risk;
- escalate uncertain cases.

---

## 14.2 Model Strategy

Albert should not rely on a single large model for everything.

Recommended approach:

- lightweight model for classification;
- stronger reasoning model for prioritization and planning;
- strong writing model for drafts;
- embeddings for semantic search and memory retrieval;
- rules engine for safety, permissions, deadlines, and hard constraints.

## 14.3 Structured Outputs

All AI extraction should return structured JSON.

Example:

```json
{
  "requires_action": true,
  "action_type": "reply_needed",
  "priority": "high",
  "urgency": "today",
  "deadline": "2026-05-21",
  "project": "Barnes Dubai Acquisition",
  "people": ["Chaker Zeraiki"],
  "recommended_next_action": "Draft clarification questions",
  "approval_required": true,
  "reason": "High-value transaction; user should review before sending."
}
```

---

# 15. Data Model

## 15.1 Core Entities

### User

Represents the Albert account holder.

Fields:

- id;
- name;
- email;
- timezone;
- preferences;
- notification settings;
- approval settings;
- created_at.

### Connected Account

Represents an external integration.

Fields:

- id;
- user_id;
- provider;
- scopes;
- token_reference;
- sync_status;
- last_synced_at.

### Message

Represents an email or later a message from another source.

Fields:

- id;
- user_id;
- source;
- external_id;
- sender;
- recipients;
- subject;
- body_summary;
- timestamp;
- thread_id;
- classification;
- priority;
- action_required;
- source_url.

### Calendar Event

Fields:

- id;
- user_id;
- external_id;
- title;
- start_time;
- end_time;
- attendees;
- location;
- description;
- prep_required;
- related_people;
- related_projects.

### Task

Fields:

- id;
- user_id;
- title;
- description;
- due_date;
- priority;
- status;
- project_id;
- source_type;
- source_id;
- created_by;
- confidence.

### Commitment

This is Albert’s most important object.

Fields:

- id;
- user_id;
- description;
- owner;
- counterparty;
- due_date;
- status;
- priority;
- source_type;
- source_id;
- evidence;
- confidence;
- created_at;
- updated_at.

Example:

```json
{
  "id": "commit_123",
  "user_id": "user_1",
  "source": "gmail",
  "source_message_id": "msg_456",
  "description": "Send signed document to Celine",
  "owner": "user",
  "counterparty": "Celine Kasparian",
  "due_date": "2026-05-21",
  "priority": "high",
  "status": "open",
  "confidence": 0.91,
  "evidence": "Could you send us the signed document before Thursday?"
}
```

### Person

Fields:

- id;
- user_id;
- name;
- email;
- organization;
- relationship_type;
- importance_weight;
- last_interaction_at;
- notes.

### Project

Fields:

- id;
- user_id;
- name;
- description;
- status;
- related_people;
- related_messages;
- related_tasks;
- related_commitments.

### Daily Briefing

Fields:

- id;
- user_id;
- date;
- summary;
- top_priorities;
- risks;
- generated_at;
- user_feedback.

### Action Proposal

Fields:

- id;
- user_id;
- action_type;
- target;
- proposed_content;
- risk_level;
- approval_required;
- status;
- created_at;
- approved_at;
- executed_at.

### Execution Log

Fields:

- id;
- user_id;
- action_proposal_id;
- action_type;
- result;
- timestamp;
- error;
- rollback_available.

---

# 16. Prioritization Logic

## 16.1 Priority Scoring Inputs

Albert should use a transparent weighted approach at first, refined by user behavior.

Potential scoring factors:

- due date proximity;
- sender importance;
- explicit urgency words;
- project importance;
- financial/legal consequences;
- user-created item vs inferred item;
- whether someone is waiting;
- repeated reminders;
- meeting proximity;
- blocker status;
- user feedback history.

## 16.2 Priority Output

Every item should receive:

- priority label;
- urgency label;
- confidence score;
- explanation;
- next action;
- recommended timing.

Example:

```json
{
  "priority": "high",
  "urgency": "today",
  "confidence": 0.87,
  "reason": "The sender asked for this before tomorrow, and it relates to an active project you marked as important.",
  "recommended_next_action": "Review and send the prepared reply."
}
```

---

# 17. Permissions and Safety

## 17.1 Default Rule

Albert may prepare actions freely, but may not execute external or sensitive actions without approval.

## 17.2 Action Categories

### Safe by Default

- summarize;
- classify;
- extract;
- recommend;
- create proposed task;
- create draft.

### Requires User Approval

- send email;
- send message;
- invite attendee;
- create calendar event with external attendees;
- modify important calendar event;
- delete anything;
- cancel meeting;
- place order;
- make payment;
- submit form.

### Never Allowed Without Strong Approval

- financial transaction;
- legal document submission;
- health decision;
- employment decision;
- irreversible account action;
- public posting;
- expensive purchase;
- cancellation with penalty.

## 17.3 Approval UI Requirements

Approval must show:

- exact action;
- recipient or platform;
- content;
- cost if any;
- reversibility;
- source evidence;
- reason for recommendation;
- alternatives.

---

# 18. Technical Architecture

## 18.1 Frontend

Recommended stack:

- React Native / Expo for mobile;
- Next.js for later web app;
- push notifications;
- voice recording;
- share sheet;
- widgets later.

## 18.2 Backend

Recommended stack:

- FastAPI or NestJS;
- PostgreSQL;
- pgvector or Qdrant for embeddings;
- Redis for queues/cache;
- Celery, BullMQ, or Temporal for background workflows;
- OAuth integration service;
- AI orchestration service;
- audit logging.

## 18.3 Core Services

### Integration Service

Handles Gmail, Calendar, and future integrations.

### Ingestion Pipeline

Fetches and normalizes data.

### AI Processing Pipeline

Classifies, extracts, summarizes, embeds, and prioritizes.

### Memory Service

Stores user preferences, people, projects, and historical context.

### Notification Service

Sends daily briefings, meeting prep alerts, and risk-based reminders.

### Execution Service

Creates drafts, tasks, calendar events, and performs approved actions.

### Approval Service

Manages human-in-the-loop approval flows.

---

# 19. API Design — Internal Concepts

## 19.1 Example Endpoints

### Get Today Dashboard

`GET /api/v1/today`

Returns:

- daily summary;
- top priorities;
- meetings;
- waiting-for items;
- quick wins;
- suggestions.

### Ask Albert

`POST /api/v1/ask`

Payload:

```json
{
  "query": "What am I forgetting?",
  "context": "today"
}
```

### Create Task

`POST /api/v1/tasks`

### Approve Action

`POST /api/v1/actions/{action_id}/approve`

### Reject Action

`POST /api/v1/actions/{action_id}/reject`

### Generate Daily Briefing

`POST /api/v1/briefings/generate`

---

# 20. Evaluation and Quality

## 20.1 Product Metrics

### Activation Metrics

- percentage of users connecting Gmail;
- percentage connecting Calendar;
- percentage receiving useful first scan;
- number of useful items found in first session;
- percentage completing first action.

### Engagement Metrics

- daily active users;
- weekly active users;
- daily briefing open rate;
- Today screen visits;
- tasks completed;
- drafts reviewed;
- drafts approved;
- reminders acted on.

### Quality Metrics

- extracted task precision;
- extracted task recall;
- priority acceptance rate;
- draft approval rate;
- meeting brief usefulness;
- false urgent rate;
- missed important item rate.

### Trust Metrics

- approval cancellation rate;
- user-reported wrong action rate;
- integration disconnect rate;
- privacy concern reports;
- notification mute rate.

## 20.2 North Star Metric

**Meaningful actions completed through Albert per active user per week.**

A meaningful action is one of:

- task completed;
- draft approved/sent;
- meeting prepared;
- follow-up sent;
- commitment resolved;
- calendar action completed;
- reminder acted on.

---

# 21. MVP Success Criteria

The MVP is successful if beta users say:

> “Albert found something I would have missed.”

Quantitative targets for private beta:

- 60%+ of users connect Gmail and Calendar.
- 50%+ of users receive at least one useful extracted item in first session.
- 40%+ weekly active usage among activated users.
- 30%+ of suggested priorities are accepted or acted on.
- 20%+ of users approve or use a generated draft weekly.
- Fewer than 10% of high-priority suggestions are marked wrong.

Qualitative targets:

- Users report feeling more in control.
- Users trust Albert enough to review it daily.
- Users ask for more integrations.
- Users ask Albert to draft or follow up.

---

# 22. Roadmap

## Phase 0 — Prototype

Timeline: 2–3 weeks

Build:

- Gmail connection;
- Calendar connection;
- basic email classification;
- commitment extraction;
- Today dashboard;
- simple Ask Albert;
- basic draft generation.

Goal:

- prove Albert can find useful obligations.

## Phase 1 — Private Beta

Timeline: 4–6 weeks

Build:

- daily briefing;
- smart reminders;
- meeting prep;
- improved priority engine;
- feedback loop;
- task management;
- approval cards;
- push notifications.

Goal:

- prove repeat weekly usage.

## Phase 2 — Mobile-First MVP

Timeline: 8–12 weeks

Build:

- polished mobile app;
- voice capture;
- share sheet;
- project grouping;
- people memory;
- better drafts;
- Notion/Todoist integration;
- subscription billing.

Goal:

- launch to early adopter community.

## Phase 3 — Execution Layer

Timeline: 3–6 months

Build:

- calendar scheduling;
- deeper task integrations;
- Slack integration;
- Google Drive context;
- approval policies;
- recurring workflows;
- delegated workflows;
- advanced follow-up system.

Goal:

- become daily operating layer.

## Phase 4 — Agentic Commerce and Services

Timeline: 6–12 months

Build:

- partner service ordering;
- delivery handoff;
- travel booking preparation;
- restaurant/grocery partner integrations;
- controlled checkout;
- spend limits;
- repeat approved actions.

Goal:

- move from productivity to trusted personal execution.

---

# 23. Launch Strategy

## 23.1 Initial Wedge

Launch with the promise:

> **Albert finds what you are forgetting in Gmail and Calendar.**

This is specific, valuable, and demoable.

## 23.2 Private Beta Audience

Start with:

- founders;
- ambitious students;
- startup operators;
- busy executives;
- users already overloaded by email/calendar.

## 23.3 Landing Page Message

Hero:

> **Stay above your priorities.**

Subheadline:

> Albert connects to your inbox and calendar, finds what matters, and helps you act before things slip.

CTA:

> Join the private beta

Proof/demo section:

1. Connect Gmail and Calendar.
2. Albert finds forgotten commitments.
3. Albert creates your Today plan.
4. Albert drafts replies and follow-ups.
5. You approve what gets sent.

## 23.4 Demo Script

1. User connects Gmail and Calendar.
2. Albert scans recent data.
3. Albert surfaces 5 open loops.
4. User clicks one high-priority item.
5. Albert explains why it matters.
6. Albert drafts a reply.
7. User approves draft.
8. Albert schedules follow-up.

The demo must show one emotional moment:

> “I would have forgotten this.”

---

# 24. Monetization

## 24.1 Consumer Pricing

### Free

- manual capture;
- limited daily briefing;
- limited integrations;
- limited history.

### Pro — €12–20/month

- Gmail + Calendar;
- daily briefings;
- priority engine;
- meeting prep;
- draft generation;
- smart reminders.

### Premium — €30–50/month

- advanced integrations;
- unlimited history;
- personal memory;
- custom workflows;
- high-volume drafting;
- priority support.

## 24.2 Professional Pricing

### Solo Professional — €25–50/month

For founders, consultants, executives, lawyers, and operators.

### Team Plan — Later

For small teams that want shared follow-up, delegation, and meeting prep.

---

# 25. Competitive Landscape

Albert competes indirectly with:

- task managers;
- calendar assistants;
- email clients;
- AI chatbots;
- note-taking apps;
- personal CRM tools;
- executive assistant services;
- productivity systems.

## 25.1 Key Differentiation

Albert is not a task manager. It creates tasks from real life.

Albert is not a chatbot. It proactively shows what matters.

Albert is not an email client. It extracts obligations from email.

Albert is not a calendar app. It prepares you for what is coming.

Albert is not a reminder app. It understands why something matters.

Albert’s differentiation is the combination of:

- cross-source context;
- commitment extraction;
- priority reasoning;
- action preparation;
- approval-based execution;
- personal memory.

---

# 26. Risks and Mitigations

## Risk 1 — Users do not trust Albert with email access

Mitigation:

- clear privacy messaging;
- minimal scopes;
- OAuth only;
- data deletion;
- transparent security page;
- local-first options later;
- no model training on user data by default.

## Risk 2 — Too many false positives

Mitigation:

- show confidence;
- use suggestions for low-confidence items;
- allow quick correction;
- optimize for precision over recall initially;
- learn from user feedback.

## Risk 3 — Too many notifications

Mitigation:

- notification controls;
- batching;
- importance thresholds;
- feedback on notification usefulness;
- quiet hours.

## Risk 4 — Generic AI assistants copy features

Mitigation:

- focus on niche wedge;
- build personal memory;
- optimize workflows deeply;
- create trust and approval layer;
- specialize in open-loop management.

## Risk 5 — Integration restrictions

Mitigation:

- start with clean APIs;
- avoid relying on fragile automation;
- use deep links where needed;
- build partner integrations later.

## Risk 6 — Liability from autonomous actions

Mitigation:

- strict approval system;
- action risk classification;
- audit logs;
- spend limits;
- no sensitive actions by default.

---

# 27. Open Questions

## Product

1. Should Albert be primarily mobile-first or web-first for the first beta?
2. Should chat be a central feature or secondary to Today?
3. Should Albert create tasks automatically or ask for confirmation first?
4. How proactive should the default notification behavior be?
5. What is the right balance between professional and personal use cases?

## Technical

1. Which integration should follow Gmail and Calendar: Notion, Todoist, Slack, or Google Drive?
2. Should the first version use pgvector inside Postgres or a dedicated vector database?
3. How much email history should Albert ingest by default?
4. How should user memory be stored and updated?
5. How should sensitive data be redacted from logs?

## Business

1. Is the first ICP founders, students, or executives?
2. What is the right price point for the private beta?
3. Should the first launch be invite-only?
4. Should Albert position as consumer productivity or professional assistant?
5. Should there be a concierge-assisted beta to learn workflows manually?

---

# 28. What Should Be Built First

The first build should not try to be everything.

The first build should prove one thing:

> **Albert can look at your inbox and calendar and tell you what you are forgetting.**

## First Build Checklist

### Must Have

- Gmail OAuth
- Calendar OAuth
- Email ingestion
- Calendar ingestion
- Task/commitment extraction
- Priority scoring
- Today dashboard
- Daily briefing
- Draft reply generation
- Approval before sending
- User feedback buttons

### Should Have

- Voice capture
- Meeting prep
- Waiting-for tracker
- Push notifications
- Project grouping

### Later

- WhatsApp workflows
- Slack
- Notion
- Todoist
- Google Drive
- commerce/order actions
- browser automation
- team workflows

---

# 29. Final Product Definition

Albert is a mobile-first AI chief of staff that helps users stay on top of their priorities by turning scattered information into clear next actions.

The product starts with Gmail and Calendar, identifies open loops, ranks priorities, prepares drafts, reminds users at the right time, and asks for approval before external actions.

Albert’s core emotional promise is:

> **You no longer feel like you are constantly forgetting something.**

Albert wins when users open it every morning and think:

> **“This is exactly what I needed to know today.”**

---

# 30. One-Sentence Build Command

Build Albert as a proactive, mobile-first AI chief of staff that connects to Gmail and Calendar, extracts commitments and priorities, shows a daily Today dashboard, prepares drafts and follow-ups, and safely executes approved actions through a strict permission system.

