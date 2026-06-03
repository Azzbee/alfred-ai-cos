// Agent companion metadata: XP, level, cosmetics, streaks.
//
// Ported from Alfred-MVP (clawbot-image-demo/web/src/agentMeta.ts) with two mobile
// adaptations:
//   1. Persistence goes through expo-secure-store (see companionMeta.ts) instead of
//      localStorage — the JWT already uses SecureStore in api/auth.ts.
//   2. Asset paths remain string constants for now; real bundled assets arrive with
//      the Lottie / SVG pack in a follow-up.
//
// Pure functions in this file stay RN-free so they can be unit-tested without a
// native runtime.

import { getEvolutionForm } from "./avatarEvolution";

/** Events that grant XP when the user interacts with Alfred. */
export type AgentEventType =
  | "agent_message_sent"
  | "task_completed"
  | "tool_used"
  | "streak_day"
  | "user_feedback_positive"
  | "shared_result";

/** Visual mood of the companion avatar — drives placeholder styling and future Lottie segments. */
export type AvatarState =
  | "idle"
  | "thinking"
  | "focused"
  | "success"
  | "error"
  | "sleep";

/** Cosmetic equipment slots unlocked as the agent levels up. */
export type CosmeticSlot = "head" | "face" | "back" | "aura" | "badge";

export type Cosmetic = {
  id: string;
  slot: CosmeticSlot;
  name: string;
  unlockLevel: number;
  icon: string;
  asset: string;
};

/** Persisted growth + inventory state for Alfred's companion avatar. */
export type AgentMeta = {
  xp: number;
  level: number;
  streakDays: number;
  lastActiveDate: string | null;
  todayCounters: Record<AgentEventType, number>;
  equipped: Partial<Record<CosmeticSlot, string>>;
  customAssets: Partial<Record<CosmeticSlot, string>>;
  inventory: string[];
  /** Theme tint color for glow / radial gradient behind the avatar orb. */
  color: string;
};

export type EventApplyResult = {
  next: AgentMeta;
  gainedXp: number;
  leveledUp: boolean;
};

/** Where the avatar is rendered in the tab shell. "home" = center + button. */
export type AvatarPlacement = "home" | "today" | "ask";

export const COSMETICS: Cosmetic[] = [
  {
    id: "head-crown",
    slot: "head",
    name: "Cloud crown",
    unlockLevel: 7,
    icon: "👑",
    asset: "/cosmetics/hat-crown.svg",
  },
  {
    id: "face-visor",
    slot: "face",
    name: "Smart visor",
    unlockLevel: 5,
    icon: "🕶️",
    asset: "/cosmetics/face-visor.svg",
  },
  {
    id: "back-pack",
    slot: "back",
    name: "Task pack",
    unlockLevel: 5,
    icon: "🎒",
    asset: "/cosmetics/back-pack.svg",
  },
  {
    id: "back-wing",
    slot: "back",
    name: "Data wings",
    unlockLevel: 10,
    icon: "🪽",
    asset: "/cosmetics/back-wing.svg",
  },
  {
    id: "aura-glow",
    slot: "aura",
    name: "Data glow",
    unlockLevel: 2,
    icon: "✨",
    asset: "/cosmetics/aura-glow.svg",
  },
  {
    id: "aura-sun",
    slot: "aura",
    name: "Orbit ring",
    unlockLevel: 9,
    icon: "☀️",
    asset: "/cosmetics/aura-sun.svg",
  },
  {
    id: "back-particles",
    slot: "back",
    name: "Data particles",
    unlockLevel: 4,
    icon: "💠",
    asset: "/cosmetics/effect-particles.svg",
  },
  {
    id: "back-ribbon",
    slot: "back",
    name: "Celebration ribbon",
    unlockLevel: 8,
    icon: "🎊",
    asset: "/cosmetics/effect-ribbon.svg",
  },
  {
    id: "badge-streak",
    slot: "badge",
    name: "Streak badge",
    unlockLevel: 5,
    icon: "🏅",
    asset: "/cosmetics/badge-streak.svg",
  },
  {
    id: "badge-pro",
    slot: "badge",
    name: "Pro collaborator",
    unlockLevel: 10,
    icon: "🛡️",
    asset: "/cosmetics/badge-pro.svg",
  },
];

/** Daily XP caps per event type — prevents farming. */
const DAILY_CAPS: Record<AgentEventType, number> = {
  agent_message_sent: 20,
  task_completed: 10,
  tool_used: 40,
  streak_day: 1,
  user_feedback_positive: 8,
  shared_result: 5,
};

/** Base XP awarded per event before streak multiplier. */
const BASE_XP: Record<AgentEventType, number> = {
  agent_message_sent: 5,
  task_completed: 40,
  tool_used: 6,
  streak_day: 20,
  user_feedback_positive: 20,
  shared_result: 35,
};

/** Cumulative XP thresholds: index i is the XP required to reach level i + 1. */
const LEVEL_THRESHOLDS = [
  0, 80, 180, 320, 520, 780, 1120, 1560, 2120, 2820, 3680, 4720,
];

function isoDay(ts: number): string {
  return new Date(ts).toISOString().slice(0, 10);
}

/** Derive level from total XP using LEVEL_THRESHOLDS. */
export function levelFromXp(xp: number): number {
  let level = 1;
  for (let i = 1; i < LEVEL_THRESHOLDS.length; i += 1) {
    if (xp >= LEVEL_THRESHOLDS[i]) level = i + 1;
  }
  return level;
}

/** XP required to reach the *next* level from the current one. */
export function nextLevelXp(level: number): number {
  const idx = Math.max(1, level);
  return LEVEL_THRESHOLDS[idx] ?? LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1];
}

/** XP floor for the current level (start of the progress bar). */
export function currentLevelXp(level: number): number {
  const idx = Math.max(0, level - 1);
  return LEVEL_THRESHOLDS[idx] ?? 0;
}

/** Bundle evolution form info for UI that shows the agent's current shape. */
export function getFormByLevel(level: number): {
  name: string;
  lottieSkin: string;
  shellAsset: string;
} {
  const form = getEvolutionForm(level);
  return {
    name: form.name,
    lottieSkin: form.lottieSkin,
    shellAsset: form.shellAsset,
  };
}

/** Visual scale / glow intensity grows with level — used by the placeholder orb. */
export function getLevelFx(level: number): {
  scale: number;
  glowBlur: number;
  glowAlpha: number;
} {
  if (level >= 10) {
    return { scale: 1.08, glowBlur: 32, glowAlpha: 0.4 };
  }
  if (level >= 5) {
    return { scale: 1.02, glowBlur: 24, glowAlpha: 0.3 };
  }
  return { scale: 1, glowBlur: 18, glowAlpha: 0.2 };
}

/** Fresh agent state for first launch or corrupt storage recovery. */
export function getDefaultMeta(): AgentMeta {
  return {
    xp: 0,
    level: 1,
    streakDays: 0,
    lastActiveDate: null,
    todayCounters: {
      agent_message_sent: 0,
      task_completed: 0,
      tool_used: 0,
      streak_day: 0,
      user_feedback_positive: 0,
      shared_result: 0,
    },
    equipped: {},
    customAssets: {},
    inventory: [],
    color: "#3A5DA8", // matches colors.accent in theme.ts
  };
}

/** Reset daily counters when the calendar day rolls over. */
function withTodayCounters(meta: AgentMeta, nowTs: number): AgentMeta {
  const today = isoDay(nowTs);
  if (meta.lastActiveDate === today) return meta;
  return {
    ...meta,
    todayCounters: {
      agent_message_sent: 0,
      task_completed: 0,
      tool_used: 0,
      streak_day: 0,
      user_feedback_positive: 0,
      shared_result: 0,
    },
  };
}

/** Auto-equip the best unlocked cosmetic per slot after level-up unlocks. */
function applyUnlocks(meta: AgentMeta): AgentMeta {
  const unlocked = COSMETICS.filter((item) => item.unlockLevel <= meta.level).map(
    (item) => item.id,
  );
  const mergedInventory = Array.from(new Set([...meta.inventory, ...unlocked]));
  const next = { ...meta, inventory: mergedInventory };

  const bySlot: Record<CosmeticSlot, Cosmetic[]> = {
    head: [],
    face: [],
    back: [],
    aura: [],
    badge: [],
  };
  for (const c of COSMETICS) bySlot[c.slot].push(c);

  const equipped = { ...next.equipped };
  (Object.keys(bySlot) as CosmeticSlot[]).forEach((slot) => {
    if (equipped[slot]) return;
    const best = bySlot[slot]
      .filter((item) => mergedInventory.includes(item.id))
      .sort((a, b) => b.unlockLevel - a.unlockLevel)[0];
    if (best) equipped[slot] = best.id;
  });

  return { ...next, equipped };
}

/** Apply an XP-granting event and return the updated meta + side-effect flags. */
export function applyEvent(
  meta: AgentMeta,
  eventType: AgentEventType,
  nowTs = Date.now(),
): EventApplyResult {
  const updated = withTodayCounters(meta, nowTs);
  const count = updated.todayCounters[eventType] ?? 0;
  const cap = DAILY_CAPS[eventType] ?? 0;

  let gainedXp = 0;
  if (count < cap) {
    const streakMultiplier = 1 + Math.min(updated.streakDays, 20) * 0.05;
    const value = BASE_XP[eventType] ?? 0;
    gainedXp = Math.round(value * streakMultiplier);
  }

  const today = isoDay(nowTs);
  let streakDays = updated.streakDays;

  if (eventType === "streak_day" && count < cap) {
    if (!updated.lastActiveDate) {
      streakDays = 1;
    } else {
      const prev = new Date(updated.lastActiveDate + "T00:00:00.000Z").getTime();
      const nowDay = new Date(today + "T00:00:00.000Z").getTime();
      const diff = Math.round((nowDay - prev) / 86_400_000);
      if (diff === 1) streakDays += 1;
      else if (diff > 1) streakDays = 1;
    }
  }

  const nextXp = updated.xp + gainedXp;
  const nextLevel = levelFromXp(nextXp);
  const leveledUp = nextLevel > updated.level;

  const next: AgentMeta = applyUnlocks({
    ...updated,
    xp: nextXp,
    level: nextLevel,
    streakDays,
    lastActiveDate: today,
    todayCounters: {
      ...updated.todayCounters,
      [eventType]: Math.min(cap, count + 1),
    },
  });

  return { next, gainedXp, leveledUp };
}

export function getCosmeticById(id?: string): Cosmetic | undefined {
  if (!id) return undefined;
  return COSMETICS.find((item) => item.id === id);
}

/** Short status copy shown near the avatar for each mood (placeholder until Lottie). */
export const AVATAR_STATE_FACE: Record<AvatarState, string> = {
  idle: "(｡•̀ᴗ-)✧",
  thinking: "( •̀ .̫ •́ )✧",
  focused: "(ง •̀_•́)ง",
  success: "٩(ˊᗜˋ*)و",
  error: "(；′⌒`)",
  sleep: "(－_－) zzZ",
};
