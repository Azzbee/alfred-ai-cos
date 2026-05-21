// Today screen: Albert's homepage (PRD principle 1, section 10.1). Loads the
// dashboard, lets the user trigger a sync, and acts on priorities.

import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { CommitmentStatus, type TodayDashboard } from "@albert/shared-types";

import { api } from "@/api/client";
import { PriorityCard } from "@/components/PriorityCard";
import { colors, spacing } from "@/theme/theme";

export function TodayScreen() {
  const [data, setData] = useState<TodayDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await api.getToday());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onSync = useCallback(async () => {
    setSyncing(true);
    try {
      await api.sync();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }, [load]);

  const updateStatus = useCallback(
    async (id: string, status: CommitmentStatus) => {
      await api.updateCommitmentStatus(id, status);
      await load();
    },
    [load],
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={syncing} onRefresh={onSync} tintColor={colors.accent} />}
    >
      <Text style={styles.heading}>Today</Text>
      {data ? <Text style={styles.summary}>{data.summary}</Text> : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.syncButton} onPress={onSync} disabled={syncing}>
        <Text style={styles.syncText}>{syncing ? "Syncing…" : "Sync Gmail"}</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Top priorities</Text>
      {data?.top_priorities.length ? (
        data.top_priorities.map((item) => (
          <PriorityCard
            key={item.id}
            item={item}
            onMarkDone={() => void updateStatus(item.id, CommitmentStatus.Done)}
            onSnooze={() => void updateStatus(item.id, CommitmentStatus.Snoozed)}
          />
        ))
      ) : (
        <Text style={styles.empty}>Nothing pressing. Sync to find open loops.</Text>
      )}

      {data?.people_waiting_on_you.length ? (
        <>
          <Text style={styles.sectionTitle}>People waiting on you</Text>
          {data.people_waiting_on_you.map((w) => (
            <Text key={w.id} style={styles.waiting}>
              {w.person ? `${w.person}: ` : ""}
              {w.description}
            </Text>
          ))}
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.md },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.bg },
  heading: { color: colors.text, fontSize: 28, fontWeight: "700" },
  summary: { color: colors.textMuted, fontSize: 14, lineHeight: 20 },
  error: { color: "#E5484D", fontSize: 13 },
  syncButton: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingVertical: spacing.sm,
    alignItems: "center",
  },
  syncText: { color: "#0E0F12", fontWeight: "600" },
  sectionTitle: { color: colors.text, fontSize: 18, fontWeight: "600", marginTop: spacing.sm },
  empty: { color: colors.textMuted, fontSize: 13, fontStyle: "italic" },
  waiting: { color: colors.textMuted, fontSize: 13 },
});
