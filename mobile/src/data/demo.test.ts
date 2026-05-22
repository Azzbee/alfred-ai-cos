import { describe, expect, it } from "vitest";

import {
  INBOX,
  SUGGESTED_QUESTIONS,
  TONE_VARIANTS,
  scriptedReply,
} from "./demo";

describe("scriptedReply routing", () => {
  it("'what am I forgetting' → aging items + Show Today action", () => {
    const r = scriptedReply("what am I forgetting?");
    expect(r.role).toBe("alfred");
    expect(r.text.toLowerCase()).toContain("aging");
    expect(r.actions?.[0]?.kind).toBe("today");
  });

  it("'who is waiting' → people + Show Today action", () => {
    const r = scriptedReply("who's waiting on me?");
    expect(r.text).toContain("Khalil");
    expect(r.actions?.[0]?.kind).toBe("today");
  });

  it("'prep for office hours' → meeting brief action", () => {
    const r = scriptedReply("help me prep for office hours");
    expect(r.actions?.[0]?.kind).toBe("meeting");
  });

  it("'what should I do first' → approval action", () => {
    const r = scriptedReply("what should I do first?");
    expect(r.actions?.[0]?.kind).toBe("approval");
  });

  it("'draft a reply' → approval action", () => {
    const r = scriptedReply("draft a reply to Khalil");
    expect(r.actions?.[0]?.kind).toBe("approval");
  });

  it("unknown question → a fallback with no actions", () => {
    const r = scriptedReply("what's the weather");
    expect(r.role).toBe("alfred");
    expect(r.actions).toBeUndefined();
  });

  it("every reply carries a timestamp", () => {
    for (const q of SUGGESTED_QUESTIONS) {
      expect(scriptedReply(q).ts).toBeTruthy();
    }
  });
});

describe("inbox fixtures", () => {
  it("every message has a category the strip knows", () => {
    const known = new Set([
      "Needs Reply",
      "Needs Decision",
      "Waiting For You",
      "FYI",
    ]);
    for (const m of INBOX) expect(known.has(m.cat)).toBe(true);
  });

  it("confidence is a probability", () => {
    for (const m of INBOX) {
      expect(m.confidence).toBeGreaterThan(0);
      expect(m.confidence).toBeLessThanOrEqual(1);
    }
  });

  it("ids are unique", () => {
    const ids = INBOX.map((m) => m.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("has at least one of each actionable category", () => {
    const cats = new Set(INBOX.map((m) => m.cat));
    expect(cats.has("Needs Reply")).toBe(true);
    expect(cats.has("Needs Decision")).toBe(true);
  });
});

describe("tone variants", () => {
  it("offers concise / warm / formal", () => {
    expect(Object.keys(TONE_VARIANTS).sort()).toEqual([
      "concise",
      "formal",
      "warm",
    ]);
  });

  it("each variant is non-empty and signs off as Maya", () => {
    for (const body of Object.values(TONE_VARIANTS)) {
      expect(body.length).toBeGreaterThan(40);
      expect(body).toMatch(/Maya/);
    }
  });
});
