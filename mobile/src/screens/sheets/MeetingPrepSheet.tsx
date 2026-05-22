// Meeting prep sheet — pixel-matched to the prototype's ScreenMeetingPrep: brief
// header, attendee avatars, context card, numbered "What to cover", open commitments.
// Wired to real getMeetingPrep(eventId). The prototype's risks/docs sections render
// only if the data carries them (the real MeetingPrep type doesn't yet, so they hide).

import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { MeetingPrep } from "@albert/shared-types";

import { api } from "@/api/client";
import { Ic, AlfMark } from "@/components/icons";
import { useShell } from "@/components/Shell";
import { ApprovalSheet } from "@/screens/sheets/ApprovalSheet";
import {
  Avatar,
  Btn,
  Eyebrow,
  H2,
  IconBtn,
  Meta,
  Serif,
} from "@/components/ui";
import { colors, fonts, spacing } from "@/theme/theme";

function whenLine(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function MeetingPrepSheet({ eventId }: { eventId: string }) {
  const { closeSheet, openSheet, showToast } = useShell();
  const [prep, setPrep] = useState<MeetingPrep | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getMeetingPrep(eventId)
      .then((p) => alive && setPrep(p))
      .catch(
        (e) =>
          alive &&
          setError(e instanceof Error ? e.message : "Failed to load prep"),
      );
    return () => {
      alive = false;
    };
  }, [eventId]);

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
        <Btn label="Close" kind="ghost" onPress={closeSheet} />
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

  const title = prep.event.title ?? "Meeting";
  return (
    <View style={styles.wrap}>
      <View style={styles.head}>
        <View style={styles.headText}>
          <Eyebrow>Meeting brief</Eyebrow>
          <H2 style={styles.title}>{title}</H2>
          <Meta style={styles.when}>
            {whenLine(prep.event.start_time)}
            {prep.event.location ? ` · ${prep.event.location}` : ""}
          </Meta>
        </View>
        <IconBtn onPress={closeSheet}>
          <Ic.Close size={16} />
        </IconBtn>
      </View>

      {prep.event.attendees.length ? (
        <View style={styles.people}>
          {prep.event.attendees.slice(0, 4).map((name) => (
            <View key={name} style={styles.person}>
              <Avatar name={name} size={32} />
              <Text style={styles.personName} numberOfLines={1}>
                {name.split(" ")[0]}
              </Text>
            </View>
          ))}
        </View>
      ) : null}

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Context */}
        <View style={styles.context}>
          <View style={styles.contextHead}>
            <AlfMark size={12} color={colors.accent} />
            <Text style={styles.contextLabel}>
              {prep.related_message_count} related message
              {prep.related_message_count === 1 ? "" : "s"}
            </Text>
          </View>
          <Serif size={15.5} color={colors.ink2} style={styles.contextText}>
            {prep.summary}
          </Serif>
        </View>

        {/* What to cover */}
        {prep.suggested_questions.length ? (
          <>
            <Text style={styles.sectionLabel}>What to cover</Text>
            <View style={styles.points}>
              {prep.suggested_questions.map((q, i) => (
                <View key={i} style={styles.point}>
                  <View style={styles.pointNum}>
                    <Text style={styles.pointNumText}>{i + 1}</Text>
                  </View>
                  <Text style={styles.pointText}>{q}</Text>
                </View>
              ))}
            </View>
          </>
        ) : null}

        {/* Open commitments */}
        {prep.open_commitments.length ? (
          <>
            <Text style={styles.sectionLabel}>Open commitments</Text>
            <View style={styles.points}>
              {prep.open_commitments.map((c, i) => (
                <View key={i} style={styles.commitRow}>
                  <Text style={styles.bullet}>·</Text>
                  <Text style={styles.commitText}>{c}</Text>
                </View>
              ))}
            </View>
          </>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <Btn
          label="Draft confirm"
          kind="ghost"
          onPress={() => {
            const attendee = prep.event.attendees[0] ?? "the organizer";
            openSheet(
              <ApprovalSheet
                recipient={attendee}
                subject={`Re: ${title}`}
                onDone={() => showToast("Sent.")}
              />,
            );
          }}
          style={styles.footerBtn}
          leading={<Ic.Mail size={12} color={colors.ink2} />}
        />
        <Btn
          label="Ready"
          kind="accent"
          onPress={closeSheet}
          style={styles.footerBtn}
          leading={<Ic.Check size={12} color="#fff" stroke={2.4} />}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flexShrink: 1, minHeight: 0 },
  centered: { paddingVertical: 60, alignItems: "center", gap: 16 },
  error: { color: colors.warn, fontSize: 14, textAlign: "center" },
  head: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  headText: { flex: 1, gap: 4 },
  title: { marginTop: 6 },
  when: { marginTop: 4 },
  people: {
    flexDirection: "row",
    gap: 14,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    marginBottom: 14,
  },
  person: { flexDirection: "row", alignItems: "center", gap: 8 },
  personName: { fontSize: 13, fontWeight: "500", color: colors.ink },
  scroll: { flexShrink: 1, minHeight: 0 },
  scrollContent: { paddingBottom: 12 },
  context: {
    backgroundColor: colors.paper2,
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
  },
  contextHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginBottom: 6,
  },
  contextLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
  },
  contextText: { lineHeight: 23 },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "500",
    letterSpacing: 0.78,
    textTransform: "uppercase",
    color: colors.ink3,
    marginBottom: 8,
  },
  points: { gap: 6, marginBottom: 18 },
  point: {
    flexDirection: "row",
    gap: 10,
    alignItems: "flex-start",
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
  },
  pointNum: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.accentSoft,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  pointNumText: {
    fontFamily: fonts.mono,
    fontSize: 11,
    color: colors.accentInk,
  },
  pointText: { flex: 1, fontSize: 14, lineHeight: 20, color: colors.ink },
  commitRow: { flexDirection: "row", gap: spacing.sm, paddingHorizontal: 4 },
  bullet: { color: colors.ink4, fontSize: 15, lineHeight: 21 },
  commitText: { flex: 1, color: colors.ink2, fontSize: 14, lineHeight: 21 },
  footer: {
    flexDirection: "row",
    gap: 8,
    paddingTop: 12,
    marginTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
  },
  footerBtn: { flex: 1 },
});
