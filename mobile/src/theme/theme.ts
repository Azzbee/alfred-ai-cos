// Albert's design tokens, ported from the Alfred prototype (warm editorial, light).
// Paper background, layered ink for text hierarchy, a single blue accent, a warm warn
// red. Instrument Serif for display, Geist Mono for metadata, system sans for body.

import type { Priority } from "@albert/shared-types";

export const colors = {
  // Surfaces (warm paper)
  paper: "#F4F1EA",
  paper2: "#EBE7DD",
  paper3: "#E0DCCF",
  card: "#FBF9F4",

  // Ink hierarchy
  ink: "#19171A",
  ink2: "#3B3A3E",
  ink3: "#6C6A70",
  ink4: "#A3A09C",

  // Hairlines
  hair: "rgba(25,23,26,0.08)",
  hair2: "rgba(25,23,26,0.14)",

  // Accent (blue) + soft tints
  accent: "#3A5DA8",
  accentSoft: "#DDE0EC", // ~accent 14% over paper, precomputed (no color-mix in RN)
  accentInk: "#16264A", // ~accent 78% + black, precomputed

  // Warn (terracotta)
  warn: "#B8543B",
  warnSoft: "#F4DCCB",

  // Success (integration "synced" dot)
  success: "#4A7A4E",
} as const;

// Named layout constants from the prototype's density-regular. Screens use these
// so the spacing reads like the spec (padX, gapCard, gapSection, cardPad).
export const layout = {
  padX: 18, // screen horizontal padding (--pad-x)
  gapCard: 12, // gap between stacked cards (--gap-card)
  gapSection: 22, // space above a section title (--gap-section)
  cardPad: 16, // card interior padding (--card-pad)
  topPad: 58, // space above the screen header (status bar + breathing room)
} as const;

// Font family keys must match the names registered in app/_layout.tsx useFonts().
export const fonts = {
  serif: "InstrumentSerif_400Regular",
  mono: "GeistMono_400Regular",
  monoMedium: "GeistMono_500Medium",
  // System sans for body text (the prototype uses -apple-system for body).
  sans: undefined as string | undefined, // undefined => RN default system font
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 22,
  xl: 32,
} as const;

export const radius = {
  card: 18,
  pill: 100,
  sm: 12,
} as const;

// Priority dot/pill colors. critical/high lean on warn (urgent), the rest on ink/accent.
export const priorityColor: Record<Priority, string> = {
  critical: "#B8543B",
  high: "#C8763B",
  medium: "#3A5DA8",
  low: "#A3A09C",
  noise: "#A3A09C",
};
