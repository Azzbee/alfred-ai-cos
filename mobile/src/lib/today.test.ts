import { describe, expect, it } from "vitest";

import { firstNameOf, greetingFor, urgencyFor } from "./today";

describe("greetingFor", () => {
  it("flips at the prototype thresholds (5 / 12 / 18)", () => {
    expect(greetingFor(2)).toBe("Still up,");
    expect(greetingFor(4)).toBe("Still up,");
    expect(greetingFor(5)).toBe("Good morning,");
    expect(greetingFor(11)).toBe("Good morning,");
    expect(greetingFor(12)).toBe("Good afternoon,");
    expect(greetingFor(17)).toBe("Good afternoon,");
    expect(greetingFor(18)).toBe("Good evening,");
    expect(greetingFor(23)).toBe("Good evening,");
  });
});

describe("urgencyFor", () => {
  const now = new Date("2026-05-19T09:00:00");

  it("high priority due today → warn Today pill", () => {
    const u = urgencyFor({ priority: "high", due_date: "2026-05-19" }, now);
    expect(u).toEqual({ label: "Today", warn: true });
  });

  it("any priority due today → warn Today pill", () => {
    const u = urgencyFor({ priority: "low", due_date: "2026-05-19" }, now);
    expect(u).toEqual({ label: "Today", warn: true });
  });

  it("high priority with no date → warn Today", () => {
    const u = urgencyFor({ priority: "critical", due_date: null }, now);
    expect(u).toEqual({ label: "Today", warn: true });
  });

  it("low priority with no date → muted Soon", () => {
    const u = urgencyFor({ priority: "low", due_date: null }, now);
    expect(u).toEqual({ label: "Soon", warn: false });
  });

  it("future date → uppercase deadline label, warn follows priority", () => {
    const u = urgencyFor({ priority: "high", due_date: "2026-05-23" }, now);
    expect(u.warn).toBe(true);
    expect(u.label).toBe(u.label.toUpperCase());
    expect(u.label).not.toBe("Today");
  });

  it("future date, low priority → not warn", () => {
    const u = urgencyFor({ priority: "low", due_date: "2026-05-23" }, now);
    expect(u.warn).toBe(false);
  });

  it("invalid date string falls back to priority", () => {
    const u = urgencyFor({ priority: "high", due_date: "not-a-date" }, now);
    expect(u).toEqual({ label: "Today", warn: true });
  });
});

describe("firstNameOf", () => {
  it("returns the first token", () => {
    expect(firstNameOf("Maya Singh")).toBe("Maya");
  });
  it("trims and collapses whitespace", () => {
    expect(firstNameOf("  Sahar  Khalil ")).toBe("Sahar");
  });
  it("returns null for empty / null / undefined", () => {
    expect(firstNameOf("")).toBeNull();
    expect(firstNameOf(null)).toBeNull();
    expect(firstNameOf(undefined)).toBeNull();
    expect(firstNameOf("   ")).toBeNull();
  });
});
