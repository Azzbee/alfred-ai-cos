// A single Today priority card (PRD 10.1). Shows title, reason, due date, and the
// actions the slice supports. "Review draft" is the path to draft -> approve.

import { Pressable, StyleSheet, Text, View } from "react-native";
import type { TodayPriority } from "@albert/shared-types";

import { colors, priorityColor, spacing } from "@/theme/theme";

type Props = {
  item: TodayPriority;
  onMarkDone: () => void;
  onSnooze: () => void;
};

export function PriorityCard({ item, onMarkDone, onSnooze }: Props) {
  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={[styles.badge, { backgroundColor: priorityColor[item.priority] }]}>
          <Text style={styles.badgeText}>{item.priority.toUpperCase()}</Text>
        </View>
        {item.due_date ? <Text style={styles.due}>Due {item.due_date}</Text> : null}
      </View>

      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.reason}>{item.reason}</Text>

      {item.confidence < 0.6 ? (
        <Text style={styles.suggestion}>Suggestion · low confidence</Text>
      ) : null}

      <View style={styles.actions}>
        <Pressable style={styles.action} onPress={onMarkDone}>
          <Text style={styles.actionText}>Mark done</Text>
        </Pressable>
        <Pressable style={styles.action} onPress={onSnooze}>
          <Text style={styles.actionText}>Snooze</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.sm,
  },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  badge: { paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: 6 },
  badgeText: { color: "#0E0F12", fontSize: 10, fontWeight: "700" },
  due: { color: colors.textMuted, fontSize: 12 },
  title: { color: colors.text, fontSize: 16, fontWeight: "600" },
  reason: { color: colors.textMuted, fontSize: 13, lineHeight: 18 },
  suggestion: { color: priorityColor.low, fontSize: 11, fontStyle: "italic" },
  actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  action: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionText: { color: colors.text, fontSize: 13 },
});
