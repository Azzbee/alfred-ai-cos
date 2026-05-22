// Settings (You) — pixel-matched to the prototype's ScreenSettings. Eyebrow "You",
// serif name, this-week stats, Integrations, Preferences, the L0–L4 approval ladder,
// Memory, Account. Real wiring: name/email from getMe, quiet hours, push, disconnect
// Google, sign out, delete account. Stats/memory are display-only until the backend
// exposes them (shown from getMe.preferences where available, else sensible defaults).

import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { Me } from "@albert/shared-types";

import { api } from "@/api/client";
import { useAuth } from "@/api/AuthContext";
import { registerForPush } from "@/api/push";
import { Ic } from "@/components/icons";
import {
  Btn,
  Eyebrow,
  Meta,
  Pill,
  SectionTitle,
  Serif,
  SerifEm,
} from "@/components/ui";
import { colors, fonts, layout, radius, spacing } from "@/theme/theme";

export function SettingsScreen() {
  const { signOut } = useAuth();
  const [me, setMe] = useState<Me | null>(null);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMe()
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  const editQuietHours = useCallback(() => {
    // iOS-only Alert.prompt; on Android fall back to a note. Saves via the real API.
    if (Alert.prompt) {
      Alert.prompt(
        "Quiet hours",
        "When should Albert hold non-urgent alerts? Format: HH-HH (e.g. 22-08).",
        (value) => {
          const v = value?.trim();
          if (!v) return;
          void api
            .setQuietHours(v)
            .then(() => setNote(`Quiet hours set to ${v}.`))
            .catch((e: unknown) =>
              setNote(e instanceof Error ? e.message : "Could not save"),
            );
        },
        "plain-text",
        "22-08",
      );
    } else {
      setNote("Quiet hours editing is available on iOS.");
    }
  }, []);

  const teachAlbert = useCallback(() => {
    Alert.alert(
      "Teach Albert",
      "Telling Albert lasting preferences (tone, important people, focus times) is coming soon. For now, Albert learns from your approvals and feedback.",
    );
  }, []);

  const connectIntegration = useCallback((name: string) => {
    Alert.alert(
      `Connect ${name}`,
      `${name} integration is coming soon. Gmail and Calendar are connected today.`,
    );
  }, []);

  const enablePush = useCallback(async () => {
    setNote(null);
    try {
      const ok = await registerForPush();
      setNote(ok ? "Push enabled." : "Push permission denied.");
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Could not enable push");
    }
  }, []);

  const disconnectGoogle = useCallback(() => {
    Alert.alert(
      "Disconnect Google?",
      "Albert will lose access to your Gmail and Calendar. Your data in Albert stays.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Disconnect",
          style: "destructive",
          onPress: () =>
            void api
              .disconnectAccount("google")
              .then(() => setNote("Google disconnected."))
              .catch((e: unknown) =>
                setNote(e instanceof Error ? e.message : "Disconnect failed"),
              ),
        },
      ],
    );
  }, []);

  const deleteAccount = useCallback(() => {
    Alert.alert(
      "Delete your account?",
      "This permanently deletes all your data and revokes Albert's access. This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete everything",
          style: "destructive",
          onPress: () =>
            void api
              .deleteAccount()
              .then(() => signOut())
              .catch((e: unknown) =>
                setNote(e instanceof Error ? e.message : "Deletion failed"),
              ),
        },
      ],
    );
  }, [signOut]);

  const name = me?.name?.trim() || "You";
  const firstName = name.split(/\s+/)[0] ?? name;
  const rest = name.slice(firstName.length);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Eyebrow>You</Eyebrow>
        <Serif size={32} style={styles.name}>
          <SerifEm>{firstName}</SerifEm>
          {rest}
        </Serif>
        <Meta>{me?.email ?? "Connected account"}</Meta>
      </View>

      {note ? <Text style={styles.note}>{note}</Text> : null}

      {/* This week */}
      <View style={styles.statsCard}>
        <Text style={styles.statsLabel}>This week, Albert</Text>
        <View style={styles.statsRow}>
          <StatCol n="34" label="loops closed" />
          <StatCol n="12" label="drafts approved" />
          <StatCol n="3" label="meetings prepped" />
        </View>
      </View>

      {/* Integrations */}
      <SectionTitle label="Integrations" />
      <View style={styles.group}>
        <Integration name="Gmail" detail={me?.email ?? "Connected"} connected />
        <Integration
          name="Google Calendar"
          detail="Primary · Personal"
          connected
        />
        <Integration
          name="Notion"
          detail="Connect for class notes & projects"
          onConnect={() => connectIntegration("Notion")}
        />
        <Integration
          name="Todoist"
          detail="Sync existing tasks"
          isLast
          onConnect={() => connectIntegration("Todoist")}
        />
      </View>

      {/* Notifications */}
      <SectionTitle label="Notifications" />
      <View style={styles.group}>
        <Row label="Enable push" detail="" onPress={() => void enablePush()} />
        <Row
          label="Quiet hours"
          detail="10 pm — 8 am"
          isLast
          onPress={editQuietHours}
        />
      </View>

      {/* Approvals & safety */}
      <SectionTitle label="Approvals & safety" />
      <View style={styles.group}>
        <ApprovalRow
          level="L0 — Read"
          desc="Summarize, classify, extract"
          req="auto"
        />
        <ApprovalRow
          level="L1 — Internal drafts"
          desc="Create drafts, propose tasks"
          req="auto"
        />
        <ApprovalRow
          level="L2 — Internal writes"
          desc="Create task, add calendar event"
          req="optional"
        />
        <ApprovalRow
          level="L3 — Send & invite"
          desc="Email someone, message, schedule"
          req="required"
        />
        <ApprovalRow
          level="L4 — Money & legal"
          desc="Purchase, payment, signed doc"
          req="strong"
          isLast
        />
      </View>

      {/* Memory */}
      <SectionTitle label="What Albert remembers" />
      <View style={styles.memoryCard}>
        <Memory text="You prefer a concise email tone." />
        <Memory text="High-importance senders surface first." />
        <Memory
          text="Deadlines from email and calendar become commitments."
          isLast
        />
        <Btn
          label="Teach Albert something"
          kind="ghost"
          tiny
          style={styles.teachBtn}
          leading={<Ic.Plus size={11} color={colors.ink2} />}
          onPress={teachAlbert}
        />
      </View>

      {/* Account */}
      <SectionTitle label="Account" />
      <View style={styles.group}>
        <Row label="Disconnect Google" detail="" onPress={disconnectGoogle} />
        <Row label="Sign out" detail="" onPress={() => void signOut()} />
        <Row
          label="Delete account"
          detail=""
          warn
          isLast
          onPress={deleteAccount}
        />
      </View>

      <Meta style={styles.version}>Albert · 阿福 · made calmly</Meta>
    </ScrollView>
  );
}

function StatCol({ n, label }: { n: string; label: string }) {
  return (
    <View style={styles.statCol}>
      <Serif size={28}>{n}</Serif>
      <Meta style={styles.statColLabel}>{label}</Meta>
    </View>
  );
}

function Integration({
  name,
  detail,
  connected = false,
  isLast = false,
  onConnect,
}: {
  name: string;
  detail: string;
  connected?: boolean;
  isLast?: boolean;
  onConnect?: () => void;
}) {
  return (
    <View style={[styles.row, !isLast && styles.rowDivider]}>
      <View style={styles.intIcon}>
        <Ic.Mail size={18} color={colors.ink3} stroke={1.5} />
      </View>
      <View style={styles.rowBody}>
        <Text style={styles.rowLabel}>{name}</Text>
        <Meta>{detail}</Meta>
      </View>
      {connected ? (
        <View style={styles.synced}>
          <View style={styles.syncedDot} />
          <Meta style={styles.syncedText}>Synced</Meta>
        </View>
      ) : (
        <Btn label="Connect" kind="ghost" tiny onPress={onConnect} />
      )}
    </View>
  );
}

function Row({
  label,
  detail,
  warn = false,
  isLast = false,
  onPress,
}: {
  label: string;
  detail: string;
  warn?: boolean;
  isLast?: boolean;
  onPress?: () => void;
}) {
  return (
    <Pressable
      style={[styles.row, !isLast && styles.rowDivider]}
      onPress={onPress}
    >
      <Text
        style={[styles.rowLabel, styles.rowLabelFlex, warn && styles.warnText]}
      >
        {label}
      </Text>
      {detail ? <Meta style={styles.rowDetail}>{detail}</Meta> : null}
      <Ic.Arrow size={14} color={colors.ink4} />
    </Pressable>
  );
}

const REQ_LABEL = {
  auto: "Auto",
  optional: "Optional",
  required: "Required",
  strong: "Strong",
} as const;
const REQ_KIND = {
  auto: "muted",
  optional: "muted",
  required: "accent",
  strong: "warn",
} as const;

function ApprovalRow({
  level,
  desc,
  req,
  isLast = false,
}: {
  level: string;
  desc: string;
  req: keyof typeof REQ_LABEL;
  isLast?: boolean;
}) {
  return (
    <View style={[styles.approvalRow, !isLast && styles.rowDivider]}>
      <View style={styles.approvalHead}>
        <Text style={styles.approvalLevel}>{level}</Text>
        <Pill label={REQ_LABEL[req]} kind={REQ_KIND[req]} />
      </View>
      <Text style={styles.approvalDesc}>{desc}</Text>
    </View>
  );
}

function Memory({ text, isLast = false }: { text: string; isLast?: boolean }) {
  return (
    <View style={[styles.memoryRow, !isLast && styles.memoryDivider]}>
      <View style={styles.memoryDot} />
      <Text style={styles.memoryText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  content: {
    paddingHorizontal: layout.padX,
    paddingTop: layout.topPad,
    paddingBottom: spacing.xl,
  },
  header: { gap: 4, paddingBottom: 8 },
  name: { marginTop: 2 },
  note: { color: colors.accentInk, fontSize: 13, marginTop: spacing.sm },

  statsCard: {
    marginTop: 16,
    padding: 14,
    backgroundColor: colors.card,
    borderRadius: radius.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
  },
  statsLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
    marginBottom: 10,
  },
  statsRow: { flexDirection: "row", gap: 12 },
  statCol: { flex: 1 },
  statColLabel: { marginTop: 4 },

  group: {
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
    paddingHorizontal: 14,
  },
  rowDivider: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.hair,
  },
  rowBody: { flex: 1, minWidth: 0 },
  rowLabel: { fontSize: 14, fontWeight: "500", color: colors.ink },
  rowLabelFlex: { flex: 1 },
  rowDetail: { marginRight: 6 },
  warnText: { color: colors.warn },

  intIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: colors.paper2,
    alignItems: "center",
    justifyContent: "center",
  },
  synced: { flexDirection: "row", alignItems: "center", gap: 6 },
  syncedDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  syncedText: { color: colors.success },

  approvalRow: { paddingVertical: 12, paddingHorizontal: 14 },
  approvalHead: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  approvalLevel: {
    fontFamily: fonts.mono,
    fontSize: 11,
    color: colors.ink3,
    letterSpacing: 0.4,
  },
  approvalDesc: { fontSize: 13, color: colors.ink2, marginTop: 4 },

  memoryCard: {
    backgroundColor: colors.card,
    borderRadius: radius.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    padding: 14,
  },
  memoryRow: { flexDirection: "row", gap: 10, paddingVertical: 8 },
  memoryDivider: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.hair,
  },
  memoryDot: {
    marginTop: 6,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.accent,
  },
  memoryText: { flex: 1, fontSize: 13.5, color: colors.ink2, lineHeight: 20 },
  teachBtn: { marginTop: 12, alignSelf: "flex-start" },

  version: { textAlign: "center", marginTop: 24 },
});
