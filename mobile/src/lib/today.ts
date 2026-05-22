// Pure, UI-free logic for the Today/priority surfaces. Extracted from the screen
// components so it can be unit-tested without a React Native runtime. The components
// import these; the tests import these. No RN, no side effects.

import type { TodayPriority } from "@albert/shared-types";

// Time-of-day greeting, matching the prototype's thresholds.
export function greetingFor(hour: number): string {
  if (hour < 5) return "Still up,";
  if (hour < 12) return "Good morning,";
  if (hour < 18) return "Good afternoon,";
  return "Good evening,";
}

// Urgency pill for a priority: warn "Today" when it's high-priority or due today,
// else an accent pill carrying the deadline. `now` is injectable for testing.
export function urgencyFor(
  item: Pick<TodayPriority, "priority" | "due_date">,
  now: Date = new Date(),
): { label: string; warn: boolean } {
  const urgent = item.priority === "critical" || item.priority === "high";
  if (!item.due_date) return { label: urgent ? "Today" : "Soon", warn: urgent };

  const due = new Date(item.due_date);
  if (Number.isNaN(due.getTime())) {
    return { label: urgent ? "Today" : "Soon", warn: urgent };
  }
  const sameDay =
    due.getFullYear() === now.getFullYear() &&
    due.getMonth() === now.getMonth() &&
    due.getDate() === now.getDate();
  if (sameDay) return { label: "Today", warn: true };

  const label = due
    .toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    })
    .toUpperCase();
  return { label, warn: urgent };
}

// First name from a full name (used in the greeting and person chips).
export function firstNameOf(name: string | null | undefined): string | null {
  const trimmed = name?.trim();
  if (!trimmed) return null;
  return trimmed.split(/\s+/)[0] ?? null;
}
