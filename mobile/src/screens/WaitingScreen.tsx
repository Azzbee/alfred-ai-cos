// Waiting-for tracker (PRD 10.1, journey 5). Two sections: people waiting on you,
// and who you are waiting on, oldest first so stale items surface. Pushed route, so
// it carries its own back button. "Draft a follow-up" opens the Approval sheet so the
// draft is visible and editable (not a silent API call).

import { useCallback, useEffect, useState } from "react";
import {
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import {
  SourceType,
  type WaitingEntry,
  type WaitingView,
} from "@albert/shared-types";

import { api } from "@/api/client";
import { Ic } from "@/components/icons";
import { useShell } from "@/components/Shell";
import { ApprovalSheet } from "@/screens/sheets/ApprovalSheet";
import {
  Avatar,
  Card,
  Eyebrow,
  IconBtn,
  Meta,
  SectionTitle,
  Serif,
} from "@/components/ui";
import { colors, layout, spacing } from "@/theme/theme";

function Entry({
  entry,
  onFollowUp,
}: {
  entry: WaitingEntry;
  onFollowUp: () => void;
}) {
  const canFollowUp =
    entry.source_type === SourceType.Gmail && Boolean(entry.source_id);
  return (
    <Card flat style={styles.entry}>
      <View style={styles.entryHead}>
        <Avatar name={entry.counterparty ?? "Someone"} size={28} />
        <View style={styles.entryBody}>
          <Text style={styles.desc}>{entry.description}</Text>
          <Meta>
            {entry.counterparty ?? "Someone"} · {entry.age_days}d old
            {entry.due_date ? ` · due ${entry.due_date}` : ""}
          </Meta>
        </View>
      </View>
      {canFollowUp ? (
        <Pressable onPress={onFollowUp} hitSlop={6} style={styles.actionPress}>
          <Text style={styles.action}>Draft a follow-up →</Text>
        </Pressable>
      ) : null}
    </Card>
  );
}

export function WaitingScreen() {
  const router = useRouter();
  const { openSheet, showToast } = useShell();
  const [view, setView] = useState<WaitingView | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setView(await api.getWaiting());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await load();
    } finally {
      setRefreshing(false);
    }
  }, [load]);

  const followUp = useCallback(
    (entry: WaitingEntry) => {
      openSheet(
        <ApprovalSheet
          recipient={entry.counterparty ?? "them"}
          subject={`Following up: ${entry.description}`}
          onDone={() => showToast("Sent.")}
        />,
      );
    },
    [openSheet, showToast],
  );

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={refresh}
          tintColor={colors.accent}
        />
      }
    >
      {/* Header with a back button (pushed route) */}
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Eyebrow>Open loops</Eyebrow>
          <Serif size={34} style={styles.title}>
            Waiting
          </Serif>
        </View>
        <IconBtn onPress={() => router.back()}>
          <Ic.Close size={18} color={colors.ink2} />
        </IconBtn>
      </View>

      <SectionTitle label="People waiting on you" />
      {view?.waiting_on_you.length ? (
        <View style={styles.stack}>
          {view.waiting_on_you.map((e) => (
            <Entry key={e.id} entry={e} onFollowUp={() => followUp(e)} />
          ))}
        </View>
      ) : (
        <Text style={styles.empty}>Nobody is blocked on you. Clean slate.</Text>
      )}

      <SectionTitle label="You are waiting on" />
      {view?.you_are_waiting_on.length ? (
        <View style={styles.stack}>
          {view.you_are_waiting_on.map((e) => (
            <Entry key={e.id} entry={e} onFollowUp={() => followUp(e)} />
          ))}
        </View>
      ) : (
        <Text style={styles.empty}>Not waiting on anyone right now.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  content: {
    paddingHorizontal: layout.padX,
    paddingTop: layout.topPad,
    paddingBottom: spacing.xl,
  },
  header: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
  },
  headerText: { flex: 1, gap: spacing.xs },
  title: { marginTop: 2 },
  stack: { gap: spacing.sm },
  empty: { color: colors.ink3, fontSize: 13, fontStyle: "italic" },
  entry: { gap: 8 },
  entryHead: { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  entryBody: { flex: 1, minWidth: 0, gap: 3 },
  desc: { color: colors.ink, fontSize: 15, lineHeight: 20 },
  actionPress: { alignSelf: "flex-start" },
  action: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: "600",
  },
});
