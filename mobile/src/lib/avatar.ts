// Pure avatar logic: deterministic tone + initials from a person's name. RN-free so
// it's unit-testable; the Avatar component (ui.tsx) imports these.

const AVATAR_TONES = [
  "#3A5DA8", // indigo
  "#2D5A3F", // forest
  "#C25B3F", // terracotta
  "#7A5AA8", // violet
  "#3F7A8C", // teal
  "#A8743A", // amber
] as const;

const FALLBACK_TONE = "#3A5DA8";

// Stable color for a name: hash the codepoints, index into the palette.
export function avatarTone(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return AVATAR_TONES[h % AVATAR_TONES.length] ?? FALLBACK_TONE;
}

// 1–2 letter initials: first two letters of a single name, or first+last initial.
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const first = parts[0];
  if (!first) return "?";
  if (parts.length === 1) return first.slice(0, 2).toUpperCase();
  const last = parts[parts.length - 1] ?? first;
  return ((first[0] ?? "") + (last[0] ?? "")).toUpperCase();
}
