// Companion avatar state shared across Today, Ask, and the tab bar home button.
//
// The center "+" on the tab bar is Alfred's companion "home". When the user is on
// Today the avatar floats top-right; on Ask it sits bottom-right; on Inbox / You it
// rests inside the home button instead of the plus glyph.
//
// Wrap the tab shell (app/(tabs)/index.tsx) with CompanionAvatarProvider so screens
// can call useCompanionAvatar() to sync mood (e.g. thinking while Ask is loading).

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  loadCompanionMeta,
  moodForContext,
  recordCompanionEvent,
  saveCompanionMeta,
} from "@/lib/companionMeta";
import {
  getDefaultMeta,
  type AgentMeta,
  type AvatarPlacement,
  type AvatarState,
} from "@/lib/agentMeta";

type CompanionAvatarApi = {
  /** Persisted XP / level / cosmetics. */
  meta: AgentMeta;
  /** Where the shell is currently showing the avatar. */
  placement: AvatarPlacement;
  /** Derived visual mood from placement + flags. */
  state: AvatarState;
  /** True while Ask is waiting on the assistant API. */
  thinking: boolean;
  /** Update which tab owns the avatar (home | today | ask). */
  setPlacement: (p: AvatarPlacement) => void;
  /** Ask screen toggles this while api.ask is in flight. */
  setThinking: (v: boolean) => void;
  /** Grant XP for an agent event and refresh meta. */
  recordEvent: (
    eventType: Parameters<typeof recordCompanionEvent>[0],
  ) => Promise<void>;
};

const CompanionAvatarContext = createContext<CompanionAvatarApi | null>(null);

export function useCompanionAvatar(): CompanionAvatarApi {
  const ctx = useContext(CompanionAvatarContext);
  if (!ctx) {
    throw new Error(
      "useCompanionAvatar must be used within <CompanionAvatarProvider>",
    );
  }
  return ctx;
}

export function CompanionAvatarProvider({ children }: { children: ReactNode }) {
  // Start with defaults so the shell renders immediately; SecureStore hydrates async.
  const [meta, setMeta] = useState<AgentMeta>(getDefaultMeta);
  const [placement, setPlacement] = useState<AvatarPlacement>("home");
  const [thinking, setThinking] = useState(false);

  // Hydrate persisted growth meta from SecureStore on mount.
  useEffect(() => {
    void loadCompanionMeta().then(setMeta);
  }, []);

  const state = moodForContext({
    placement,
    thinking,
    sleeping: false,
  });

  const recordEvent = useCallback<
    CompanionAvatarApi["recordEvent"]
  >(async (eventType) => {
    const result = await recordCompanionEvent(eventType);
    setMeta(result.meta);
  }, []);

  const api = useMemo<CompanionAvatarApi>(
    () => ({
      meta,
      placement,
      state,
      thinking,
      setPlacement,
      setThinking,
      recordEvent,
    }),
    [meta, placement, state, thinking, recordEvent],
  );

  return (
    <CompanionAvatarContext.Provider value={api}>
      {children}
    </CompanionAvatarContext.Provider>
  );
}
/** Optional helper: persist a color tweak from a future settings sheet. */
export async function updateCompanionColor(color: string): Promise<AgentMeta> {
  const current = await loadCompanionMeta();
  const next = { ...current, color };
  await saveCompanionMeta(next);
  return next;
}
