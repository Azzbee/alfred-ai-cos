# Albert mobile — design reference

The single source of truth for the editorial light theme. Ported verbatim from the
Alfred interactive prototype (the `proto_*` / `css_*` scratch files). When the
implementation and this doc disagree, this doc wins; if the doc is wrong, fix the doc.

## Tokens (exact hex from the prototype `--vars`)

| Token        | Value                          | Use |
|--------------|--------------------------------|-----|
| paper        | `#f4f1ea`                      | screen background |
| paper2       | `#ebe7dd`                      | quoted blocks, mode-tab track, recent rows |
| paper3       | `#e0dccf`                      | (reserved) |
| card         | `#fbf9f4`                      | card surface |
| ink          | `#19171a`                      | primary text, ink buttons |
| ink2         | `#3b3a3e`                      | body text |
| ink3         | `#6c6a70`                      | meta, secondary |
| ink4         | `#a3a09c`                      | faint meta, check border, rank numbers |
| hair         | `rgba(25,23,26,0.08)`          | card hairline, dividers |
| hair2        | `rgba(25,23,26,0.14)`          | flat-card border, input border |
| accent       | `#3a5da8`                      | indigo accent (default; tweakable) |
| accentSoft   | `#dde0ec` (= accent 14% on paper, precomputed) | accent pill bg, soft cards |
| accentInk    | `#16264a` (= accent 78% + black, precomputed)  | accent pill text, em in titles |
| warn         | `#b8543b`                      | terracotta: urgency, danger, delete |
| warnSoft     | `#f4dccb`                      | warn pill bg, risk blocks |
| success      | `#4a7a4e`                      | integration "synced" dot |

RN has no `color-mix`, so `accentSoft`/`accentInk` are precomputed. Accent is
tweakable in the prototype (Ink/Indigo/Forest/Terracotta); we ship Indigo.

## Type

- **serif** = Instrument Serif 400. Display: greetings, titles, priority titles,
  briefing prose, transcripts (italic). `letterSpacing: -0.01em`, `lineHeight ~1.15`.
  `em` inside a title is italic + `accentInk`.
- **mono** = Geist Mono. Eyebrows (`11px / 0.14em / uppercase / ink3`), meta
  (`12px / ink3`), pill text (`10.5px / 0.04em / uppercase`), rank numbers, tab labels
  (`9px / 0.1em / uppercase`), section "WHY" label (`10px / 0.08em`).
- **sans** = system. Body, `h3` section titles (`13px / 500 / 0.06em / uppercase / ink3`),
  buttons (`14px / 500`).

## Spacing / radius (regular density)

`padX 18`, `gapCard 12`, `gapSection 22`, `cardPad 16`. Radius: card `18`, flat-card
`14`, pill `100`, input/sheet-inner `12-16`, sheet `26` (top corners only).

## Components (the `alf-*` classes → RN primitives in `ui.tsx`)

- **Serif / Eyebrow / Meta / SectionTitle (`h3`)** — text primitives.
- **Card** (`alf-card`): card bg, radius 18, pad 16, hairline border + soft shadow.
  **Card flat** (`alf-card-flat`): transparent, radius 14, hair2 border.
- **Pill** kinds: `accent` (soft bg / accentInk / accent border), `warn`,
  `muted` (transparent / ink3 / hair2 border). Optional leading `dot` (5px, currentColor).
  Mono uppercase. A non-mono variant exists (inbox cats, "I'll listen for" chips): sans, none-transform.
- **Btn** kinds: `ink` (ink bg / paper text — default), `accent` (accent / white),
  `ghost` (transparent / ink2 / hair2 border). Sizes: regular, `tiny` (12px / 6-10 pad),
  `full` (100% width). `:active` scale 0.97. Disabled opacity 0.4.
- **Check** (`alf-check`): 22px circle, 1.2px ink4 border; done = accent fill + white tick.
- **IconBtn** (`alf-icon-btn`): 36px circle, card bg, hair2 border, soft shadow.
- **Avatar**: colored circle, initials, white, `fontSize = size*0.36`, weight 600.
  Color from person's `tone`.
- **TabBar** (`alf-tabbar`): 5 slots — Today, Inbox, **center Capture (+)**, Ask, You.
  Tab = mono 9px uppercase, ink4 default / accent active, icon above label. Center
  Capture is an ink circle 52px, lifted `-18px`, paper ring + shadow. Top hairline.
- **Sheet** (`alf-sheet`): bottom sheet over the screen. Backdrop ink@34% + blur, slide-up
  0.28s. Paper bg, top radius 26, grab handle (38x4, ink4@40%). Holds MeetingPrep / Approval.
- **Toast** (`alf-toast`): ink pill, paper text, centered above tab bar, check icon, pop-in,
  auto-dismiss ~2.2s.
- **AlfMark**: the Albert logo glyph (used in pills, suggestions, chat, capture).

## Screens

1. **Today (Stacked)** — eyebrow date, serif "Good morning, *Name*.", subtitle,
   count strip (3 stats), "What matters today" + PriorityCards, "Waiting on you"
   card (avatars), "Quick wins" rows, "Alfred suggests" (proactive). FooterStamp.
2. **Inbox** — eyebrow, serif "What *matters*.", category strip, briefing banner,
   expandable MessageCards (Alfred's take + confidence, preview, actions).
3. **Ask** — eyebrow, serif "What's on your *mind?*", chat bubbles (Alfred serif/left,
   user ink-pill/right), suggested questions, composer with accent send.
4. **Capture** — full-screen over tabs. Modes (Speak/Type/Snap/Forward). Voice idle
   (breathing rings + mic), recording (ink bg, timer, waveform), parsed (transcript +
   detected chips + extracted task cards + confirm).
5. **Settings (You)** — eyebrow, serif "*Name* Singh", week stats, Integrations,
   Preferences, Approvals & safety (L0-L4), Memory, Account.
6. **MeetingPrep** (sheet) — brief, people, context, talking points, risks, docs.
7. **Approval** (sheet) — email draft, tone selector (concise/warm/formal), evidence,
   risk note, send/save.
8. **Onboarding / Briefing / Connect** — calibration, daily briefing hero, OAuth entry.

## Behaviors

- Greeting by hour: <5 "Still up," / <12 "Good morning," / <18 "Good afternoon," / else "Good evening,".
- Priority urgency `today` → warn pill "Today"; else accent pill with the deadline.
- markDone toggles + toast "Marked done." snooze → toast "Snoozed until tomorrow."
- Real data: prototype's fake people/emails are replaced by live Gmail/Calendar;
  the visual treatment is identical.
