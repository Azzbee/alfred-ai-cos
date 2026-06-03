// Secure persistence for Alfred's companion agent metadata.
//
// Uses secureStorage.ts (Keychain on native, localStorage on web dev).

import {
  readSecureItem,
  writeSecureItem,
} from "@/lib/secureStorage";

import {
  applyEvent,
  getDefaultMeta,
  type AgentEventType,
  type AgentMeta,
  type AvatarState,
} from "./agentMeta";

const META_KEY = "albert.companion.meta";

/** Read persisted meta, merging with defaults and stripping invalid cosmetic ids. */
export async function loadCompanionMeta(): Promise<AgentMeta> {
  try {
    const raw = await readSecureItem(META_KEY);
    if (!raw) return getDefaultMeta();
    const merged = { ...getDefaultMeta(), ...JSON.parse(raw) } as AgentMeta;
    return merged;
  } catch {
    return getDefaultMeta();
  }
}

/** Persist meta after XP events or cosmetic changes. */
export async function saveCompanionMeta(meta: AgentMeta): Promise<void> {
  await writeSecureItem(META_KEY, JSON.stringify(meta));
}

/** Convenience: load → applyEvent → save → return result. */
export async function recordCompanionEvent(
  eventType: AgentEventType,
): Promise<{ meta: AgentMeta; gainedXp: number; leveledUp: boolean }> {
  const current = await loadCompanionMeta();
  const { next, gainedXp, leveledUp } = applyEvent(current, eventType);
  await saveCompanionMeta(next);
  return { meta: next, gainedXp, leveledUp };
}

/** Map tab context to the avatar's visual mood. */
export function moodForContext(opts: {
  placement: "home" | "today" | "ask";
  thinking: boolean;
  sleeping: boolean;
}): AvatarState {
  if (opts.sleeping) return "sleep";
  if (opts.thinking) return "thinking";
  // Default idle everywhere — "focused" will map to Lottie segments when tasks run.
  return "idle";
}
