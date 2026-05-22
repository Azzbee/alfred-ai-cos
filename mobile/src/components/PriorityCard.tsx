// A single Today priority card, pixel-matched to the Alfred prototype's PriorityCard:
// circular check, urgency pill (warn "Today" / accent deadline), optional person
// avatar+name from counterparty, serif title, mono "WHY" + reason, Act/Snooze/Not
// important. Real backend fields (TodayPriority); the prototype's fake "minutes" is
// omitted since the backend doesn't provide it.

import { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import type { TodayPriority } from "@albert/shared-types";

import { Avatar, Btn, Card, Check, Meta, Pill, Serif } from "@/components/ui";
import { urgencyFor } from "@/lib/today";
import { colors, fonts, spacing } from "@/theme/theme";

type Props = {
  item: TodayPriority;
  done?: boolean;
  onAct: () => void;
  onMarkDone: () => void;
  onSnooze: () => void;
  onDismiss?: () => void;
};

export function PriorityCard({
  item,
  done = false,
  onAct,
  onMarkDone,
  onSnooze,
  onDismiss,
}: Props) {
  const u = urgencyFor(item);
  // Fade to 0.55 when completed (prototype's `transition: opacity .25s`).
  const opacity = useRef(new Animated.Value(done ? 0.55 : 1)).current;
  useEffect(() => {
    Animated.timing(opacity, {
      toValue: done ? 0.55 : 1,
      duration: 250,
      useNativeDriver: true,
    }).start();
  }, [done, opacity]);

  return (
    <Animated.View style={{ opacity }}>
      <Card>
        <View style={styles.row}>
          <Check done={done} onPress={onMarkDone} style={styles.check} />
          <View style={styles.body}>
            <View style={styles.metaRow}>
              <Pill label={u.label} kind={u.warn ? "warn" : "accent"} dot />
              {item.confidence < 0.6 ? (
                <Text style={styles.suggestion}>suggestion</Text>
              ) : null}
              {item.counterparty ? (
                <View style={styles.person}>
                  <Avatar name={item.counterparty} size={20} />
                  <Meta>{item.counterparty.split(" ")[0]}</Meta>
                </View>
              ) : null}
            </View>

            <Serif
              size={18}
              color={done ? colors.ink4 : colors.ink}
              style={[styles.title, done && styles.titleDone]}
            >
              {item.title}
            </Serif>

            <Text style={styles.reasonWrap}>
              <Text style={styles.whyLabel}>WHY </Text>
              <Text style={styles.reason}>{item.reason}</Text>
            </Text>

            <View style={styles.actions}>
              <Btn label="Act" kind="accent" tiny onPress={onAct} />
              <Btn label="Snooze" kind="ghost" tiny onPress={onSnooze} />
              {onDismiss ? (
                <Btn
                  label="Not important"
                  kind="ghost"
                  tiny
                  onPress={onDismiss}
                />
              ) : null}
            </View>
          </View>
        </View>
      </Card>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.md },
  check: { marginTop: 2 },
  body: { flex: 1, minWidth: 0, gap: 6 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  suggestion: {
    fontFamily: fonts.mono,
    fontSize: 10,
    color: colors.ink4,
    fontStyle: "italic",
  },
  person: {
    marginLeft: "auto",
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  title: { marginTop: 2 },
  titleDone: { textDecorationLine: "line-through" },
  reasonWrap: { marginTop: 2 },
  whyLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 0.8,
    color: colors.ink4,
  },
  reason: { fontSize: 13, lineHeight: 19, color: colors.ink3 },
  actions: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.sm,
    flexWrap: "wrap",
  },
});
