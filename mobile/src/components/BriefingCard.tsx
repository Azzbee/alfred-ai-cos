// Daily briefing (PRD 12.7), editorial variant from the Alfred prototype: a mono
// eyebrow, a large serif "Good morning.", and the summary set in serif at reading size.
// The morning hero. A quiet usefulness ask sits below, collapsing once answered.

import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { Briefing } from "@albert/shared-types";

import { api } from "@/api/client";
import { Btn, Eyebrow, Serif } from "@/components/ui";
import { colors, fonts, spacing } from "@/theme/theme";

function greeting(): string {
  const h = new Date().getHours();
  if (h < 5) return "Still up.";
  if (h < 12) return "Good morning.";
  if (h < 18) return "Good afternoon.";
  return "Good evening.";
}

function dateLine(iso: string | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

export function BriefingCard() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setBriefing(await api.getTodayBriefing());
    } catch {
      setBriefing(null);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const generate = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      setBriefing(await api.generateBriefing());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't write your briefing");
    } finally {
      setBusy(false);
    }
  }, []);

  const sendFeedback = useCallback(
    async (useful: boolean) => {
      if (!briefing) return;
      setBriefing(await api.briefingFeedback(briefing.id, useful));
    },
    [briefing],
  );

  // Empty / generating
  if (!briefing) {
    return (
      <View style={styles.wrap}>
        <Eyebrow>{dateLine(new Date().toISOString())}</Eyebrow>
        <Serif size={40} style={styles.heading}>
          {greeting()}
        </Serif>
        <Text style={styles.lead}>
          {busy
            ? "Reading your inbox and calendar…"
            : "I haven't written today's briefing yet."}
        </Text>
        {busy ? (
          <ActivityIndicator color={colors.accent} style={styles.spinner} />
        ) : (
          <View style={styles.ctaRow}>
            <Btn
              label="Write today's briefing"
              kind="accent"
              onPress={generate}
            />
          </View>
        )}
        {error ? <Text style={styles.error}>{error}</Text> : null}
      </View>
    );
  }

  // Present
  const answered = briefing.user_feedback != null;
  return (
    <View style={styles.wrap}>
      <Eyebrow>
        {dateLine(briefing.date)
          ? `${dateLine(briefing.date)} · a briefing`
          : "a briefing"}
      </Eyebrow>
      <Serif size={40} style={styles.heading}>
        {greeting()}
      </Serif>
      <Serif size={20} color={colors.ink2} style={styles.summary}>
        {briefing.summary}
      </Serif>

      <View style={styles.feedbackRow}>
        {answered ? (
          <Text style={styles.thanks}>
            {briefing.user_feedback === "useful"
              ? "Glad it helped."
              : "Noted, I'll tune it."}
          </Text>
        ) : (
          <>
            <Text style={styles.ask}>Was this useful?</Text>
            <Pressable hitSlop={8} onPress={() => void sendFeedback(true)}>
              <Text style={styles.yes}>Yes</Text>
            </Pressable>
            <Pressable hitSlop={8} onPress={() => void sendFeedback(false)}>
              <Text style={styles.no}>No</Text>
            </Pressable>
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingVertical: spacing.sm, gap: spacing.sm },
  heading: { marginTop: spacing.sm },
  // The summary is the hero: serif, reading size, generous leading.
  summary: { marginTop: spacing.md, lineHeight: 27 },
  lead: {
    marginTop: spacing.sm,
    fontSize: 16,
    lineHeight: 24,
    color: colors.ink2,
  },
  spinner: { alignSelf: "flex-start", marginTop: spacing.md },
  ctaRow: { flexDirection: "row", marginTop: spacing.md },
  error: { color: colors.warn, fontSize: 13, marginTop: spacing.sm },

  feedbackRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    marginTop: spacing.lg,
  },
  ask: {
    fontFamily: fonts.mono,
    fontSize: 12,
    color: colors.ink3,
    marginRight: "auto",
  },
  yes: { color: colors.accent, fontSize: 13, fontWeight: "600" },
  no: { color: colors.ink3, fontSize: 13, fontWeight: "600" },
  thanks: { fontSize: 13, fontStyle: "italic", color: colors.ink3 },
});
