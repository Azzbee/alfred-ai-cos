// Inbox — the Priority Inbox, pixel-matched to the Alfred prototype. Eyebrow, serif
// "What matters.", category strip with live counts, a briefing banner, and expandable
// message cards (Albert's take + preview + actions).
//
// Real data: GET /messages returns the user's synced, classified Gmail. Categories are
// the backend's MessageClassification collapsed into four buckets. The per-message
// "confidence %" and "suggested action" from the prototype are omitted — no real source.

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  LayoutAnimation,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  UIManager,
  View,
} from "react-native";
import type { InboxMessage } from "@albert/shared-types";

import { api } from "@/api/client";
import { ApprovalSheet } from "@/screens/sheets/ApprovalSheet";
import { AlfMark } from "@/components/icons";
import { useShell } from "@/components/Shell";
import {
  Avatar,
  Btn,
  Eyebrow,
  FooterStamp,
  Meta,
  Pill,
  Serif,
  SerifEm,
} from "@/components/ui";
import { colors, fonts, layout, radius, spacing } from "@/theme/theme";

// LayoutAnimation opt-in for old-arch Android; harmless elsewhere.
if (
  Platform.OS === "android" &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}
const ease = () =>
  LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);

type Category = InboxMessage["category"];

const CATS: { id: string; label: string; match: Category | null }[] = [
  { id: "all", label: "All", match: null },
  { id: "reply", label: "Needs Reply", match: "Needs Reply" },
  { id: "decide", label: "Needs Decision", match: "Needs Decision" },
  { id: "wait", label: "Waiting", match: "Waiting" },
  { id: "fyi", label: "FYI", match: "FYI" },
];

function catPill(cat: Category): "warn" | "accent" | "muted" {
  if (cat === "Needs Reply") return "warn";
  if (cat === "Needs Decision") return "accent";
  return "muted";
}

// Short relative age, e.g. "4h", "2d", from an ISO timestamp.
function ago(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (mins < 60) return `${mins}m`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.round(hrs / 24)}d`;
}

export function InboxScreen() {
  const { openSheet, showToast } = useShell();
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [filteredCount, setFilteredCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cat, setCat] = useState<string>("all");
  const [open, setOpen] = useState<string | null>(null);
  const [archived, setArchived] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      setError(null);
      const view = await api.getInbox();
      setMessages(view.messages);
      setFilteredCount(view.filtered_count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load your inbox");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const live = useMemo(
    () => messages.filter((m) => !archived.has(m.id)),
    [messages, archived],
  );
  const shown = useMemo(() => {
    const c = CATS.find((x) => x.id === cat);
    if (!c || c.match === null) return live;
    return live.filter((m) => m.category === c.match);
  }, [live, cat]);

  const counts = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const c of CATS) {
      acc[c.id] =
        c.match === null
          ? live.length
          : live.filter((m) => m.category === c.match).length;
    }
    return acc;
  }, [live]);

  const archive = (id: string, msg = "Archived.") => {
    ease();
    setArchived((s) => new Set(s).add(id));
    showToast(msg);
  };

  const replyCount = counts["reply"] ?? 0;
  const decideCount = counts["decide"] ?? 0;
  const briefing =
    `${replyCount} need${replyCount === 1 ? "s" : ""} a reply. ` +
    `${decideCount} ${decideCount === 1 ? "is a decision" : "are decisions"} to make. ` +
    `I filtered ${filteredCount} newsletter${filteredCount === 1 ? "" : "s"}.`;

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
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Eyebrow>Priority Inbox</Eyebrow>
        <Serif size={32} style={styles.title}>
          What <SerifEm>matters</SerifEm>.
        </Serif>
      </View>

      {/* Category strip */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.catStripScroll}
        contentContainerStyle={styles.catStrip}
      >
        {CATS.map((c) => (
          <Pill
            key={c.id}
            label={`${c.label}  ${counts[c.id] ?? 0}`}
            kind={cat === c.id ? "accent" : "muted"}
            mono={false}
            onPress={() => setCat(c.id)}
            style={styles.catPill}
          />
        ))}
      </ScrollView>

      {/* Briefing banner (only meaningful with messages) */}
      {live.length || filteredCount ? (
        <View style={styles.banner}>
          <AlfMark size={18} filled color={colors.accent} />
          <Serif size={16} color={colors.ink2} style={styles.bannerText}>
            {briefing}
          </Serif>
        </View>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {shown.map((m) => (
        <MessageCard
          key={m.id}
          msg={m}
          expanded={open === m.id}
          onToggle={() => {
            ease();
            setOpen(open === m.id ? null : m.id);
          }}
          onDraft={() =>
            openSheet(
              <ApprovalSheet
                recipient={m.sender}
                subject={m.subject ? `Re: ${m.subject}` : "Re:"}
                onDone={() => showToast("Sent.")}
              />,
            )
          }
          onArchive={() => archive(m.id)}
          onSnooze={() => archive(m.id, "Snoozed.")}
        />
      ))}

      {shown.length === 0 ? (
        <View style={styles.zero}>
          <Serif size={18} italic color={colors.ink3}>
            {live.length ? "Inbox zero, in this category." : "Inbox zero."}
          </Serif>
          <Meta>
            {live.length
              ? "Quite the feeling, isn't it."
              : "Nothing synced yet — pull from Today to sync."}
          </Meta>
        </View>
      ) : null}

      <FooterStamp />
    </ScrollView>
  );
}

function MessageCard({
  msg,
  expanded,
  onToggle,
  onDraft,
  onArchive,
  onSnooze,
}: {
  msg: InboxMessage;
  expanded: boolean;
  onToggle: () => void;
  onDraft: () => void;
  onArchive: () => void;
  onSnooze: () => void;
}) {
  return (
    <View style={styles.msgCard}>
      <Pressable style={styles.msgHead} onPress={onToggle}>
        <Avatar name={msg.sender} size={36} />
        <View style={styles.msgBody}>
          <View style={styles.msgTopRow}>
            <Text style={styles.msgFrom} numberOfLines={1}>
              {msg.sender}
            </Text>
            <Meta>{ago(msg.sent_at)}</Meta>
          </View>
          {msg.subject ? (
            <Text style={styles.msgSubject}>{msg.subject}</Text>
          ) : null}
          <View style={styles.msgMetaRow}>
            <Pill label={msg.category} kind={catPill(msg.category)} />
          </View>

          {expanded ? (
            <View style={styles.expanded}>
              {msg.take ? (
                <View style={styles.take}>
                  <View style={styles.takeHead}>
                    <AlfMark size={12} color={colors.accent} />
                    <Text style={styles.takeLabel}>Albert's take</Text>
                  </View>
                  <Text style={styles.takeText}>{msg.take}</Text>
                </View>
              ) : null}
              {msg.snippet ? (
                <Text style={styles.preview}>{msg.snippet}</Text>
              ) : null}
              <View style={styles.msgActions}>
                {msg.category === "Needs Reply" ? (
                  <Btn
                    label="Draft reply"
                    kind="accent"
                    tiny
                    onPress={onDraft}
                  />
                ) : null}
                {msg.category === "Needs Decision" ? (
                  <>
                    <Btn label="Yes" kind="accent" tiny onPress={onArchive} />
                    <Btn label="No" kind="ghost" tiny onPress={onArchive} />
                  </>
                ) : null}
                <Btn label="Snooze" kind="ghost" tiny onPress={onSnooze} />
                <Btn label="Archive" kind="ghost" tiny onPress={onArchive} />
              </View>
            </View>
          ) : null}
        </View>
      </Pressable>
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
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.paper,
  },
  header: { gap: 6, paddingBottom: 6 },
  title: { marginTop: 2 },

  catStripScroll: {
    marginHorizontal: -layout.padX,
    marginTop: 8,
    marginBottom: 14,
  },
  catStrip: { gap: 6, paddingHorizontal: layout.padX },
  catPill: { paddingHorizontal: 12, paddingVertical: 6 },

  banner: {
    flexDirection: "row",
    gap: 10,
    alignItems: "flex-start",
    backgroundColor: colors.accentSoft,
    borderRadius: radius.card,
    padding: layout.cardPad,
    marginBottom: 12,
  },
  bannerText: { flex: 1, lineHeight: 22 },
  error: { color: colors.warn, fontSize: 13, marginBottom: 12 },

  msgCard: {
    backgroundColor: colors.card,
    borderRadius: 16,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    overflow: "hidden",
  },
  msgHead: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    padding: 14,
  },
  msgBody: { flex: 1, minWidth: 0 },
  msgTopRow: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: 6,
  },
  msgFrom: { flex: 1, fontSize: 14, fontWeight: "500", color: colors.ink },
  msgSubject: {
    fontSize: 14,
    color: colors.ink2,
    marginTop: 2,
    lineHeight: 18,
  },
  msgMetaRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 8,
    alignItems: "center",
  },

  expanded: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
  },
  take: {
    backgroundColor: colors.paper2,
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
  },
  takeHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginBottom: 6,
  },
  takeLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
  },
  takeText: { fontSize: 13.5, lineHeight: 19, color: colors.ink },
  preview: {
    fontSize: 13,
    color: colors.ink3,
    lineHeight: 20,
    marginBottom: 12,
  },
  msgActions: { flexDirection: "row", gap: 8, flexWrap: "wrap" },

  zero: { alignItems: "center", paddingVertical: 40, gap: 6 },
});
