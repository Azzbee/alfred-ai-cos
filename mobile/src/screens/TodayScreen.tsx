// Today — the Stacked variant, pixel-matched to the Alfred prototype. Eyebrow date,
// serif greeting with the user's name, subtitle, count strip, "What matters today"
// priority cards, "Waiting on you" (avatars), "Quick wins", "Alfred suggests", footer.
// Real backend data throughout (TodayDashboard + listTasks + getMe).

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import {
  CommitmentStatus,
  TaskStatus,
  type Me,
  type Task,
  type TodayDashboard,
} from "@albert/shared-types";

import { api } from "@/api/client";
import { Ic } from "@/components/icons";
import { PriorityCard } from "@/components/PriorityCard";
import { useShell } from "@/components/Shell";
import { firstNameOf, greetingFor } from "@/lib/today";
import { MeetingPrepSheet } from "@/screens/sheets/MeetingPrepSheet";
import {
  Avatar,
  Card,
  Check,
  Eyebrow,
  FooterStamp,
  Meta,
  Pill,
  SectionTitle,
  Serif,
  SerifEm,
} from "@/components/ui";
import { colors, layout, radius, spacing } from "@/theme/theme";

function todayLine(): string {
  return new Date()
    .toLocaleDateString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
    })
    .toUpperCase();
}

export function TodayScreen() {
  const router = useRouter();
  const { openSheet, showToast } = useShell();
  const [me, setMe] = useState<Me | null>(null);
  const [data, setData] = useState<TodayDashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Ids tapped-done locally: the check fills + the row/card fades immediately. The
  // real API write is deferred (see commitTimers) so an Undo can cancel it before it
  // commits — a misclick on "done" is fully reversible during the grace window.
  const [completing, setCompleting] = useState<Set<string>>(new Set());
  const commitTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  // Cancel a pending completion (Undo): clear the deferred write and un-fade the item.
  const undoComplete = useCallback((id: string) => {
    const timer = commitTimers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      commitTimers.current.delete(id);
    }
    setCompleting((s) => {
      const next = new Set(s);
      next.delete(id);
      return next;
    });
  }, []);

  // Clean up any in-flight commit timers on unmount.
  useEffect(() => {
    const timers = commitTimers.current;
    return () => timers.forEach((t) => clearTimeout(t));
  }, []);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [dashboard, pending, taskList, profile] = await Promise.all([
        api.getToday(),
        api.listPendingActions(),
        api.listTasks().catch(() => [] as Task[]),
        api.getMe().catch(() => null),
      ]);
      setData(dashboard);
      setPendingCount(pending.length);
      setTasks(taskList);
      setMe(profile);
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

  const markPriorityDone = useCallback(
    (id: string) => {
      // Fade immediately, defer the write so Undo can catch a misclick.
      setCompleting((s) => new Set(s).add(id));
      const timer = setTimeout(() => {
        commitTimers.current.delete(id);
        api
          .updateCommitmentStatus(id, CommitmentStatus.Done)
          .then(() => load())
          .catch((e: unknown) => {
            undoComplete(id);
            setError(e instanceof Error ? e.message : "Couldn't update");
          });
      }, 4000);
      commitTimers.current.set(id, timer);
      showToast("Marked done.", {
        action: { label: "Undo", onPress: () => undoComplete(id) },
        duration: 4000,
      });
    },
    [load, showToast, undoComplete],
  );

  const snoozePriority = useCallback(
    async (id: string) => {
      await api.updateCommitmentStatus(id, CommitmentStatus.Snoozed);
      showToast("Snoozed until tomorrow.");
      await load();
    },
    [load, showToast],
  );

  const completeQuickWin = useCallback(
    (task: Task) => {
      // Fade immediately, defer the write so Undo can catch a misclick.
      setCompleting((s) => new Set(s).add(task.id));
      const timer = setTimeout(() => {
        commitTimers.current.delete(task.id);
        api
          .updateTaskStatus(task.id, TaskStatus.Done)
          .then(() => load())
          .catch((e: unknown) => {
            undoComplete(task.id);
            setError(e instanceof Error ? e.message : "Couldn't update task");
          });
      }, 4000);
      commitTimers.current.set(task.id, timer);
      showToast("Marked done.", {
        action: { label: "Undo", onPress: () => undoComplete(task.id) },
        duration: 4000,
      });
    },
    [load, showToast, undoComplete],
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  const firstName = firstNameOf(me?.name);
  const quickWins = tasks.filter(
    (t) => t.priority === "low" && t.status !== TaskStatus.Done,
  );
  const waiting = data?.people_waiting_on_you ?? [];

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={syncing}
          onRefresh={onSync}
          tintColor={colors.accent}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Eyebrow>{todayLine()}</Eyebrow>
        <Serif size={36} style={styles.greeting}>
          {greetingFor(new Date().getHours())}{" "}
          {firstName ? (
            <SerifEm>{firstName}</SerifEm>
          ) : (
            <SerifEm>there</SerifEm>
          )}
          .
        </Serif>
        {data?.summary ? (
          <Text style={styles.subtitle}>{data.summary}</Text>
        ) : null}
      </View>

      {/* Count strip */}
      {data ? (
        <View style={styles.countStrip}>
          <Stat n={data.top_priorities.length} label="matter today" />
          <Stat n={data.people_waiting_on_you.length} label="waiting on you" />
          <Stat n={data.meetings_to_prepare.length} label="meetings" />
        </View>
      ) : null}

      {/* Pending approvals banner */}
      {pendingCount > 0 ? (
        <Pressable
          style={styles.approvalsBanner}
          onPress={() => router.push("/approvals")}
        >
          <Text style={styles.approvalsText}>
            {pendingCount} action{pendingCount === 1 ? "" : "s"} await your
            approval
          </Text>
          <Ic.Arrow size={16} color={colors.warn} />
        </Pressable>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {/* What matters today */}
      <SectionTitle
        label="What matters today"
        right={<Meta>{data?.top_priorities.length ?? 0} open</Meta>}
      />
      {data?.top_priorities.length ? (
        <View style={styles.cardStack}>
          {data.top_priorities.map((item) => (
            <PriorityCard
              key={item.id}
              item={item}
              done={completing.has(item.id)}
              onAct={() => router.push("/approvals")}
              onMarkDone={() => void markPriorityDone(item.id)}
              onSnooze={() => void snoozePriority(item.id)}
            />
          ))}
        </View>
      ) : (
        <Text style={styles.empty}>
          Nothing pressing. Pull to sync and find open loops.
        </Text>
      )}

      {/* Waiting on you */}
      {waiting.length ? (
        <>
          <SectionTitle
            label="Waiting on you"
            right={
              <Pill
                label="View all"
                kind="muted"
                mono={false}
                onPress={() => router.push("/waiting")}
              />
            }
          />
          <Card style={styles.list}>
            {waiting.map((w, i) => (
              <Pressable
                key={w.id}
                onPress={() => router.push("/waiting")}
                style={({ pressed }) => [
                  styles.waitRow,
                  i > 0 && styles.rowDivider,
                  pressed && styles.rowPressed,
                ]}
              >
                <Avatar name={w.person ?? "Someone"} size={32} />
                <View style={styles.waitBody}>
                  <Text style={styles.waitText}>{w.description}</Text>
                  {w.person ? <Meta>{w.person}</Meta> : null}
                </View>
                <Ic.Arrow size={16} color={colors.ink4} />
              </Pressable>
            ))}
          </Card>
        </>
      ) : null}

      {/* Quick wins */}
      {quickWins.length ? (
        <>
          <SectionTitle
            label="Quick wins"
            right={<Meta>{quickWins.length} small</Meta>}
          />
          <View style={styles.quickStack}>
            {quickWins.map((t) => (
              <QuickWinRow
                key={t.id}
                title={t.title}
                done={completing.has(t.id)}
                onDone={() => void completeQuickWin(t)}
              />
            ))}
          </View>
        </>
      ) : null}

      {/* Meetings to prepare */}
      {data?.meetings_to_prepare.length ? (
        <>
          <SectionTitle label="Meetings to prepare" />
          <View style={styles.cardStack}>
            {data.meetings_to_prepare.map((m) => (
              <Card
                key={m.id}
                flat
                style={styles.meeting}
                onPress={() => openSheet(<MeetingPrepSheet eventId={m.id} />)}
              >
                <Serif size={16}>{m.title ?? "Meeting"}</Serif>
                {m.start_time ? (
                  <Meta>{new Date(m.start_time).toLocaleString()}</Meta>
                ) : null}
              </Card>
            ))}
          </View>
        </>
      ) : null}

      <FooterStamp />
    </ScrollView>
  );
}

function Stat({ n, label }: { n: number; label: string }) {
  return (
    <View style={styles.stat}>
      <Serif size={26}>{String(n)}</Serif>
      <Meta>{label}</Meta>
    </View>
  );
}

// A quick-win row: the Check animates its fill on tap, the row fades + strikes through
// while the optimistic completion settles.
function QuickWinRow({
  title,
  done,
  onDone,
}: {
  title: string;
  done: boolean;
  onDone: () => void;
}) {
  const opacity = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.timing(opacity, {
      toValue: done ? 0.5 : 1,
      duration: 250,
      useNativeDriver: true,
    }).start();
  }, [done, opacity]);
  return (
    <Animated.View style={[styles.quickRow, { opacity }]}>
      <Check done={done} onPress={onDone} />
      <Text style={[styles.quickText, done && styles.quickTextDone]}>
        {title}
      </Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  content: {
    paddingHorizontal: layout.padX,
    paddingTop: layout.topPad,
    paddingBottom: spacing.xl,
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.paper,
  },
  header: { gap: 10, paddingBottom: 14 },
  greeting: { marginTop: 2 },
  subtitle: { fontSize: 15, lineHeight: 22, color: colors.ink3, maxWidth: 320 },
  error: { color: colors.warn, fontSize: 13, marginTop: spacing.sm },

  countStrip: { flexDirection: "row", gap: spacing.sm, marginTop: 4 },
  stat: {
    flex: 1,
    gap: 2,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
  },

  cardStack: { gap: layout.gapCard },
  quickStack: { gap: 6 },

  approvalsBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.warnSoft,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
    marginTop: spacing.md,
  },
  approvalsText: {
    flex: 1,
    color: colors.warn,
    fontWeight: "600",
    fontSize: 13,
  },

  empty: { color: colors.ink3, fontSize: 13, fontStyle: "italic" },

  list: { padding: 0 },
  waitRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  rowDivider: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
  },
  rowPressed: { backgroundColor: colors.paper2 },
  waitBody: { flex: 1, minWidth: 0, gap: 2 },
  waitText: { color: colors.ink, fontSize: 14, lineHeight: 19 },

  quickRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
  },
  quickText: { flex: 1, color: colors.ink, fontSize: 14 },
  quickTextDone: { textDecorationLine: "line-through", color: colors.ink4 },

  meeting: { gap: 3 },
});
