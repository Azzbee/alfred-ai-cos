// Action approval queue (PRD 10.6, 17.3). Each pending action shows what it does,
// its content, and its risk. Level 4-5 actions require an explicit second confirm.
// Editorial theme: danger maps to the warn (terracotta) palette, risk to a mono pill.

import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { ActionProposal } from "@albert/shared-types";

import { api } from "@/api/client";
import { Btn, Card, Pill, ScreenHeader, Serif } from "@/components/ui";
import { colors, fonts, radius, spacing } from "@/theme/theme";

const RISK_LABEL: Record<number, string> = {
  0: "Read-only",
  1: "Internal prep",
  2: "Reversible",
  3: "External",
  4: "Financial",
  5: "Sensitive",
};

function ActionCard({
  action,
  onApprove,
  onReject,
}: {
  action: ActionProposal;
  onApprove: () => void;
  onReject: () => void;
}) {
  const danger = action.strong_confirmation;
  return (
    <Card style={danger ? styles.cardDanger : undefined}>
      <View style={styles.headerRow}>
        <Serif size={17}>{action.action_type}</Serif>
        <Pill
          label={RISK_LABEL[action.risk_level] ?? `Level ${action.risk_level}`}
          kind={danger ? "warn" : "muted"}
        />
      </View>
      {action.reason ? (
        <Text style={styles.reason}>{action.reason}</Text>
      ) : null}
      {action.proposed_content ? (
        <Text style={styles.cardContent} numberOfLines={6}>
          {action.proposed_content}
        </Text>
      ) : null}
      {danger ? (
        <Text style={styles.warning}>
          This is irreversible or financial. You'll be asked to confirm again.
        </Text>
      ) : null}
      <View style={styles.actions}>
        <View style={styles.actionSlot}>
          <Btn label="Reject" kind="ghost" onPress={onReject} />
        </View>
        <View style={styles.actionSlot}>
          {danger ? (
            <Pressable style={styles.approveDanger} onPress={onApprove}>
              <Text style={styles.approveDangerText}>Approve…</Text>
            </Pressable>
          ) : (
            <Btn label="Approve" kind="accent" onPress={onApprove} />
          )}
        </View>
      </View>
    </Card>
  );
}

export function ActionApprovalScreen() {
  const [actions, setActions] = useState<ActionProposal[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setActions(await api.listPendingActions());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load actions");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const approve = useCallback(
    async (action: ActionProposal) => {
      const run = async (confirm: boolean) => {
        try {
          await api.approveAction(action.id, confirm);
          await load();
        } catch (e) {
          setError(e instanceof Error ? e.message : "Approval failed");
        }
      };
      if (action.strong_confirmation) {
        Alert.alert(
          "Confirm this action",
          "This is irreversible or moves money. Are you sure?",
          [
            { text: "Cancel", style: "cancel" },
            {
              text: "Yes, do it",
              style: "destructive",
              onPress: () => void run(true),
            },
          ],
        );
      } else {
        await run(false);
      }
    },
    [load],
  );

  const reject = useCallback(
    async (action: ActionProposal) => {
      await api.rejectAction(action.id);
      await load();
    },
    [load],
  );

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <ScreenHeader eyebrow="Needs you" title="Approvals" />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {actions.length ? (
        <View style={styles.stack}>
          {actions.map((a) => (
            <ActionCard
              key={a.id}
              action={a}
              onApprove={() => void approve(a)}
              onReject={() => void reject(a)}
            />
          ))}
        </View>
      ) : (
        <Text style={styles.empty}>Nothing waiting for your approval.</Text>
      )}
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
  stack: { gap: spacing.md },
  error: { color: colors.warn, fontSize: 13, marginTop: spacing.sm },
  empty: { color: colors.ink3, fontSize: 13, fontStyle: "italic" },
  cardDanger: { borderColor: colors.warn },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  reason: { color: colors.ink3, fontSize: 13, lineHeight: 18 },
  // The proposed draft, set apart as a quoted block on a slightly deeper paper.
  cardContent: {
    color: colors.ink2,
    fontSize: 13,
    lineHeight: 19,
    backgroundColor: colors.paper2,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  warning: {
    fontFamily: fonts.mono,
    color: colors.warn,
    fontSize: 11.5,
    lineHeight: 16,
    marginTop: spacing.sm,
  },
  actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  actionSlot: { flex: 1 },
  approveDanger: {
    backgroundColor: colors.warn,
    borderRadius: radius.pill,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  approveDangerText: { color: "#FFFFFF", fontSize: 14, fontWeight: "600" },
});
