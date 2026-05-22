// Scripted demo data for the Inbox and Ask screens. These two surfaces have no
// backend yet (no inbox / chat / suggestions routes), so they render from these
// fixtures, matching the Alfred prototype exactly. When the backend ships those
// routes, swap these for real API calls; the screen components don't change shape.
//
// The content mirrors the prototype's ALF_INBOX / ALF_SUGGESTED_QUESTIONS / scripted
// reply logic verbatim.

export type InboxCategory =
  | "Needs Reply"
  | "Needs Decision"
  | "Waiting For You"
  | "FYI";

export type InboxMessage = {
  id: string;
  from: string; // sender name (drives the avatar)
  subject: string;
  received: string; // "17h", "6h", "1d"
  cat: InboxCategory;
  deadline: string; // "Today", "By Thu", "—"
  confidence: number; // 0..1
  summary: string; // Alfred's take
  action: string; // suggested action
  preview: string; // email body preview
};

export const INBOX: InboxMessage[] = [
  {
    id: "m1",
    from: "Sahar Khalil",
    subject: "Re: Thesis check-in — Thursday",
    received: "17h",
    cat: "Needs Reply",
    deadline: "Today",
    confidence: 0.93,
    summary:
      "Prof. Khalil wants to move Thursday to 2pm and asks you to bring the updated outline so you can finalize the topic form.",
    action: "send a one-line yes and attach the v3 outline.",
    preview:
      "Can we move Thursday to 2pm? I have a faculty meeting at 11. Also bring your updated outline so we can finalize the topic form.",
  },
  {
    id: "m2",
    from: "Priya Shah",
    subject: "Anthropic — onsite scheduling",
    received: "6h",
    cat: "Needs Decision",
    deadline: "By Thu",
    confidence: 0.88,
    summary:
      "Recruiting is offering two onsite dates. Picking the later one gives you a clearer week before midterms.",
    action: "pick May 30; it avoids the Calc III crunch.",
    preview:
      "We'd love to host you onsite. Does May 23 or May 30 work better? Happy to cover travel either way.",
  },
  {
    id: "m3",
    from: "CS Women McGill",
    subject: "Mixer Wed — RSVP by tonight",
    received: "4h",
    cat: "Needs Decision",
    deadline: "Tonight",
    confidence: 0.71,
    summary:
      "A one-tap RSVP for Wednesday's mixer. You've gone to the last two and tagged the group as important.",
    action: "RSVP yes; it's on a light evening for you.",
    preview:
      "Our spring mixer is this Wednesday at 6pm in Trottier. RSVP by tonight so we can finalize the count.",
  },
  {
    id: "m4",
    from: "Daniel Ortega",
    subject: "A3 regrade — could you send the original PDF?",
    received: "1d",
    cat: "Waiting For You",
    deadline: "No rush",
    confidence: 0.8,
    summary:
      "Daniel is blocked on your original A3 PDF before he can file the regrade. It's sitting in your Drive.",
    action: "send the PDF from Drive; I can attach it.",
    preview:
      "Hey, for the regrade I just need the original A3 submission PDF. Could you forward it when you get a sec?",
  },
  {
    id: "m5",
    from: "Mom",
    subject: "flight??",
    received: "2d",
    cat: "Needs Reply",
    deadline: "By Sun",
    confidence: 0.85,
    summary:
      "Mom is asking about your flight home for reading week. United fares for that Friday rose 18% overnight.",
    action: "confirm the Friday morning flight before fares climb more.",
    preview: "did you book the flight home yet? let me know the dates xx",
  },
  {
    id: "m6",
    from: "Lena Park",
    subject: "Figma — design intern stage 2",
    received: "3d",
    cat: "FYI",
    deadline: "—",
    confidence: 0.6,
    summary:
      "Figma moved you to stage 2 of the design internship. No action needed yet; they'll send a scheduling link.",
    action: "no reply needed; I'll flag the link when it lands.",
    preview:
      "Congrats — you've advanced to stage 2. Expect a scheduling link from our team next week.",
  },
  {
    id: "m7",
    from: "McGill Housing",
    subject: "Lease renewal window opens June 1",
    received: "4d",
    cat: "FYI",
    deadline: "Jun 8",
    confidence: 0.55,
    summary:
      "Your lease renewal window opens June 1 and closes June 8. No decision needed this week.",
    action: "I'll remind you on June 1.",
    preview:
      "The renewal window for your unit opens June 1. Renew by June 8 to keep your current rate.",
  },
];

export const INBOX_BRIEFING =
  "2 need a reply today. 2 are decisions you can make in under a minute. I filtered 41 newsletters this week.";

// ── Ask Alfred ───────────────────────────────────────────────────────────────

export const SUGGESTED_QUESTIONS = [
  "What am I forgetting?",
  "Who's waiting on me?",
  "Help me prep for office hours",
  "What should I do first?",
];

export type ChatMessage = {
  role: "user" | "alfred";
  text: string;
  ts: string;
  actions?: { label: string; kind: "today" | "meeting" | "approval" }[];
};

export const CHAT_SEED: ChatMessage[] = [
  {
    role: "alfred",
    text: "Morning. Quieter than yesterday — three things matter, and one of them is a one-line reply. Ask me anything, or tap a suggestion.",
    ts: "now",
  },
];

// The prototype's scripted intelligence. Matches scriptedReply / scriptedActions.
export function scriptedReply(q: string): ChatMessage {
  const s = q.toLowerCase();
  if (s.includes("forget")) {
    return {
      role: "alfred",
      ts: "now",
      text: "Three things are aging: Prof. Khalil's Thursday confirmation (17h, she's waiting), the Anthropic essay (closes Friday — 240 words to go), and the flight home Mom asked about Sunday. The Khalil one is the only one with a deadline today.",
      actions: [{ label: "Show Today", kind: "today" }],
    };
  }
  if (s.includes("waiting") || s.includes("who")) {
    return {
      role: "alfred",
      ts: "now",
      text: "Three people. Prof. Khalil since yesterday — moving Thursday to 2pm. Chen for half of the COMP 421 write-up, three days now. Mom about the flight home. Khalil first; she has a faculty meeting at 11.",
      actions: [{ label: "Show Today", kind: "today" }],
    };
  }
  if (s.includes("prep") || s.includes("office")) {
    return {
      role: "alfred",
      ts: "now",
      text: "Office hours with Sahar at 11. Bring the updated outline (v3, narrowed to two case studies), confirm Thursday 2pm works, and ask about Prof. Devlin as co-advisor. I'll pull the full brief if you want it.",
      actions: [{ label: "Open meeting brief", kind: "meeting" }],
    };
  }
  if (s.includes("first") || s.includes("start")) {
    return {
      role: "alfred",
      ts: "now",
      text: "Reply to Sahar. It's a one-line yes plus the outline attached — I drafted it. After that, the Anthropic essay has the most reward per minute.",
      actions: [{ label: "Review draft for Sahar", kind: "approval" }],
    };
  }
  if (s.includes("draft") || s.includes("reply") || s.includes("khalil")) {
    return {
      role: "alfred",
      ts: "now",
      text: "I have drafts ready for Sahar, Mom, and a 1-tap RSVP for the CS Women mixer. Daniel's regrade is waiting on you sending him the original PDF — I can pull it from Drive.",
      actions: [{ label: "Review draft for Sahar", kind: "approval" }],
    };
  }
  return {
    role: "alfred",
    ts: "now",
    text: "I can do that. Want me to look at Today, the inbox, or your calendar?",
  };
}

// ── Demo email draft (for the Approval sheet when opened without a real draft) ──

export const DEMO_DRAFT = {
  to: "sahar.khalil@mcgill.ca",
  subject: "Re: Thesis check-in — Thursday",
  attachments: ["thesis-outline-v3.pdf"],
  tone: "concise" as const,
  evidenceFrom: "From Sahar, yesterday at 4:18 pm",
  evidence:
    "Can we move Thursday to 2pm? I have a faculty meeting at 11. Also bring your updated outline so we can finalize the topic form.",
};

export const TONE_VARIANTS: Record<string, string> = {
  concise: [
    "Hi Prof. Khalil,",
    "",
    "2pm Thursday works — I'll just need to leave at 2:45 sharp for COMP 421 lab.",
    "",
    "I've attached the updated outline (v3). The big change is narrowing to two case studies, like you suggested. Would also love your read on whether Prof. Devlin makes sense as a co-advisor, or whether that's overreach for an undergrad thesis.",
    "",
    "See you Thursday,",
    "Maya",
  ].join("\n"),
  warm: [
    "Hi Prof. Khalil,",
    "",
    "Thursday at 2pm works perfectly — thank you for the heads up about the faculty meeting. I'll just need to slip out by 2:45 for my COMP 421 lab, but that gives us a solid 45 minutes.",
    "",
    "I've attached the updated outline (v3) — narrowed to two case studies, as you suggested. I'd also love to get your honest read on whether Prof. Devlin could realistically co-advise, or whether that's a bit ambitious for an undergrad thesis.",
    "",
    "Really looking forward to Thursday,",
    "Maya",
  ].join("\n"),
  formal: [
    "Dear Professor Khalil,",
    "",
    "Thank you for the note. Thursday at 2:00 PM works for me; I will need to leave by 2:45 PM to attend my COMP 421 laboratory.",
    "",
    "Please find attached the revised thesis outline (v3). The principal revision is the narrowing of scope to two case studies, per your previous guidance. I would also welcome your assessment of whether Professor Devlin would be an appropriate co-advisor.",
    "",
    "With thanks,",
    "Maya Singh",
  ].join("\n"),
};
