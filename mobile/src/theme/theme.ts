// Minimal design tokens. Albert's surface should feel calm (PRD principle 6),
// so the palette is restrained and priority color is reserved for signal.

import type { Priority } from "@albert/shared-types";

export const colors = {
  bg: "#0E0F12",
  surface: "#1A1C20",
  text: "#F4F5F7",
  textMuted: "#9AA0A6",
  border: "#2A2D33",
  accent: "#5B8DEF",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const priorityColor: Record<Priority, string> = {
  critical: "#E5484D",
  high: "#F5A623",
  medium: "#5B8DEF",
  low: "#9AA0A6",
  noise: "#5C616B",
};
