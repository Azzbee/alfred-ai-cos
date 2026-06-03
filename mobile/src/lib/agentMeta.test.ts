import { describe, expect, it } from "vitest";

import {
  applyEvent,
  getDefaultMeta,
  levelFromXp,
  nextLevelXp,
} from "./agentMeta";

describe("levelFromXp", () => {
  it("starts at level 1 with zero XP", () => {
    expect(levelFromXp(0)).toBe(1);
  });

  it("levels up at the first threshold (80 XP)", () => {
    expect(levelFromXp(79)).toBe(1);
    expect(levelFromXp(80)).toBe(2);
  });
});

describe("applyEvent", () => {
  it("grants XP for agent_message_sent", () => {
    const meta = getDefaultMeta();
    const { next, gainedXp } = applyEvent(meta, "agent_message_sent");
    expect(gainedXp).toBeGreaterThan(0);
    expect(next.xp).toBe(meta.xp + gainedXp);
  });
});

describe("nextLevelXp", () => {
  it("returns the threshold for level 2", () => {
    expect(nextLevelXp(1)).toBe(80);
  });
});
