// Meeting prep brief (PRD 10.5). Loads context, open commitments, and suggested
// questions for one upcoming event. Editorial theme: serif title + summary, mono meta.

import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { MeetingPrep } from "@albert/shared-types";

import { api } from "@/api/client";
import { Eyebrow, Meta, SectionTitle, Serif } from "@/components/ui";
import { colors, spacing } from "@/theme/theme";

function dateLine(iso: string | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function MeetingPrepScreen({ eventId }: { eventId: string }) {
  const [prep, setPrep] = useState<MeetingPrep | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPrep(await api.getMeetingPrep(eventId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load prep");
    }
  }, [eventId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }
  if (!prep) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Eyebrow>Meeting prep</Eyebrow>
      <Serif size={30} style={styles.title}>
        {prep.event.title ?? "Meeting"}
      </Serif>
      {prep.event.start_time ? (
        <Meta style={styles.when}>{dateLine(prep.event.start_time)}</Meta>
      ) : null}
      <Meta>
        {prep.related_message_count} related message
        {prep.related_message_count === 1 ? "" : "s"} ·{" "}
        {prep.event.attendees.length} attendee
        {prep.event.attendees.length === 1 ? "" : "s"}
      </Meta>

      <SectionTitle label="Context" />
      <Serif size={18} color={colors.ink2} style={styles.summary}>
        {prep.summary}
      </Serif>

      {prep.open_commitments.length ? (
        <>
          <SectionTitle label="Open commitments" />
          <View style={styles.list}>
            {prep.open_commitments.map((c, i) => (
              <View key={i} style={styles.bulletRow}>
                <Text style={styles.bullet}>·</Text>
                <Text style={styles.item}>{c}</Text>
              </View>
            ))}
          </View>
        </>
      ) : null}

      {prep.suggested_questions.length ? (
        <>
          <SectionTitle label="Suggested questions" />
          <View style={styles.list}>
            {prep.suggested_questions.map((q, i) => (
              <View key={i} style={styles.bulletRow}>
                <Text style={styles.bullet}>·</Text>
                <Text style={styles.item}>{q}</Text>
              </View>
            ))}
          </View>
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  content: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.paper,
  },
  title: { marginTop: 2, marginBottom: spacing.xs },
  when: { marginBottom: 2 },
  summary: { marginTop: spacing.sm, lineHeight: 25 },
  list: { gap: 6 },
  bulletRow: { flexDirection: "row", gap: spacing.sm },
  bullet: { color: colors.ink4, fontSize: 15, lineHeight: 21 },
  item: { flex: 1, color: colors.ink2, fontSize: 15, lineHeight: 21 },
  error: { color: colors.warn, fontSize: 14, padding: spacing.lg },
});
