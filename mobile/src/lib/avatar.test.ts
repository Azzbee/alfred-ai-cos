import { describe, expect, it } from "vitest";

import { avatarTone, initials } from "./avatar";

describe("avatarTone", () => {
  it("is stable for the same name", () => {
    expect(avatarTone("Sahar Khalil")).toBe(avatarTone("Sahar Khalil"));
  });

  it("returns a hex color from the palette", () => {
    expect(avatarTone("Priya Shah")).toMatch(/^#[0-9A-F]{6}$/i);
  });

  it("varies across different names (not all identical)", () => {
    const names = ["Sahar", "Priya", "Daniel", "Mom", "Chen", "Lena"];
    const tones = new Set(names.map(avatarTone));
    expect(tones.size).toBeGreaterThan(1);
  });

  it("handles an empty string without throwing", () => {
    expect(avatarTone("")).toMatch(/^#[0-9A-F]{6}$/i);
  });
});

describe("initials", () => {
  it("takes first + last initial for a full name", () => {
    expect(initials("Sahar Khalil")).toBe("SK");
  });

  it("takes the first two letters of a single name", () => {
    expect(initials("Mom")).toBe("MO");
  });

  it("uppercases", () => {
    expect(initials("daniel ortega")).toBe("DO");
  });

  it("uses first + last across three or more words", () => {
    expect(initials("CS Women McGill")).toBe("CM");
  });

  it("collapses extra whitespace", () => {
    expect(initials("  Priya   Shah  ")).toBe("PS");
  });

  it("returns ? for an empty name", () => {
    expect(initials("")).toBe("?");
    expect(initials("   ")).toBe("?");
  });
});
