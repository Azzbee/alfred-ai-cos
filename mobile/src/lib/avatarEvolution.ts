// Avatar evolution forms and animation segment mapping.
//
// Ported from Alfred-MVP (clawbot-image-demo/web/src/avatarEvolution.ts).
// The mobile app does not load Lottie yet — this module defines the data model
// so future animation work can plug in without reshaping call sites.
//
// Each evolution form unlocks at a minimum agent level and points at shell/Lottie
// assets (web paths today; swap for require() or bundled assets on native later).

import type { AvatarState } from "./agentMeta";

/** One visual "form" the companion avatar can evolve into. */
export type EvolutionForm = {
  /** Minimum agent level required to use this form. */
  minLevel: number;
  /** Human-readable label shown in growth UI (future). */
  name: string;
  /** Static shell illustration (SVG). Placeholder until Lottie ships. */
  shellAsset: string;
  /** Lottie JSON filename under /lottie/ on web; not bundled on mobile yet. */
  lottieSkin: string;
};

/** How a given AvatarState maps onto Lottie frame segments + optional overlay. */
export type EvolutionState = {
  /** Inclusive frame range inside the Lottie timeline. */
  segment: [number, number];
  /** Optional SVG overlay for thinking / success / error / sleep. */
  overlayAsset?: string;
  loop?: boolean;
  speed?: number;
};

/** Ordered list of forms; getEvolutionForm picks the highest minLevel the agent qualifies for. */
export const EVOLUTION_FORMS: EvolutionForm[] = [
  {
    minLevel: 1,
    name: "Cloud core",
    shellAsset: "/avatar-pack/evo-core-lv1.svg",
    lottieSkin: "cloud-core-base.json",
  },
  {
    minLevel: 5,
    name: "Cloud core · advanced",
    shellAsset: "/avatar-pack/evo-core-lv5.svg",
    lottieSkin: "cloud-core-base.json",
  },
  {
    minLevel: 10,
    name: "Cloud core · awakened",
    shellAsset: "/avatar-pack/evo-core-lv10.svg",
    lottieSkin: "cloud-core-base.json",
  },
];

/** Per-state animation config — consumed by AgentAvatarCard on web; reserved for RN Lottie. */
export const EVOLUTION_STATES: Record<AvatarState, EvolutionState> = {
  idle: { segment: [0, 44], loop: true, speed: 0.86 },
  focused: { segment: [45, 89], loop: true, speed: 0.92 },
  thinking: {
    segment: [90, 134],
    overlayAsset: "/avatar-pack/state-thinking.svg",
    loop: true,
    speed: 0.82,
  },
  success: {
    segment: [135, 179],
    overlayAsset: "/avatar-pack/state-success.svg",
    loop: false,
    speed: 1.02,
  },
  error: {
    segment: [45, 89],
    overlayAsset: "/avatar-pack/state-error.svg",
    loop: true,
    speed: 0.78,
  },
  sleep: {
    segment: [0, 24],
    overlayAsset: "/avatar-pack/state-sleep.svg",
    loop: true,
    speed: 0.68,
  },
};

/** Resolve the best evolution form for the agent's current level. */
export function getEvolutionForm(level: number): EvolutionForm {
  let form = EVOLUTION_FORMS[0];
  for (const item of EVOLUTION_FORMS) {
    if (level >= item.minLevel) form = item;
  }
  return form;
}
