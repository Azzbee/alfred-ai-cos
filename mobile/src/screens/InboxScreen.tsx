// Inbox — the Priority Inbox, pixel-matched to the Alfred prototype. Eyebrow,
// serif "What matters.", category strip with counts, Alfred briefing banner, and
// expandable message cards (Alfred's take + confidence, preview, actions).
//
// Runs on scripted fixtures (src/data/demo.ts) because no inbox backend exists yet.
// The Approval sheet opens from "Draft reply". See DESIGN.md.

import { useMemo, useState } from "react";
import {
  LayoutAnimation,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  UIManager,
  View,
} from "react-native";

// LayoutAnimation needs an opt-in on old-arch Android; harmless elsewhere.
if (
  Platform.OS === "android" &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// A gentle ease for expand/collapse and message removal.
const ease = () =>
  LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);

import { INBOX, INBOX_BRIEFING, type InboxMessage } from "@/data/demo";
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

const CATS = [
  { id: "all", label: "All", match: null },
  { id: "reply", label: "Needs Reply", match: "Needs Reply" },
  { id: "decide", label: "Needs Decision", match: "Needs Decision" },
  { id: "wait", label: "Waiting", match: "Waiting For You" },
  { id: "fyi", label: "FYI", match: "FYI" },
] as const;

function catPill(cat: InboxMessage["cat"]): "warn" | "accent" | "muted" {
  if (cat === "Needs Reply") return "warn";
  if (cat === "Needs Decision") return "accent";
  return "muted";
}

export function InboxScreen() {
  const { openSheet, showToast } = useShell();
  const [cat, setCat] = useState<string>("all");
  const [open, setOpen] = useState<string | null>(null);
  const [archived, setArchived] = useState<Set<string>>(new Set());

  const live = useMemo(
    () => INBOX.filter((m) => !archived.has(m.id)),
    [archived],
  );
  const filtered = useMemo(() => {
    const c = CATS.find((x) => x.id === cat);
    if (!c || c.match === null) return live;
    return live.filter((m) => m.cat === c.match);
  }, [live, cat]);

  const counts = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const c of CATS) {
      acc[c.id] =
        c.match === null
          ? live.length
          : live.filter((m) => m.cat === c.match).length;
    }
    return acc;
  }, [live]);

  const archive = (id: string, msg = "Archived.") => {
    ease();
    setArchived((s) => new Set(s).add(id));
    showToast(msg);
  };

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Eyebrow>Priority Inbox · Gmail synced 4m ago</Eyebrow>
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

      {/* Briefing banner */}
      <View style={styles.banner}>
        <AlfMark size={18} filled color={colors.accent} />
        <Serif size={16} color={colors.ink2} style={styles.bannerText}>
          {INBOX_BRIEFING}
        </Serif>
      </View>

      {/* Messages */}
      {filtered.map((m) => (
        <MessageCard
          key={m.id}
          msg={m}
          expanded={open === m.id}
          onToggle={() => {
            ease();
            setOpen(open === m.id ? null : m.id);
          }}
          onDraft={() =>
            openSheet(<ApprovalSheet onDone={() => showToast("Sent.")} />)
          }
          onArchive={() => archive(m.id)}
          onSnooze={() => archive(m.id, "Snoozed.")}
        />
      ))}
      {filtered.length === 0 ? (
        <View style={styles.zero}>
          <Serif size={18} italic color={colors.ink3}>
            Inbox zero, in this category.
          </Serif>
          <Meta>Quite the feeling, isn't it.</Meta>
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
        <Avatar name={msg.from} size={36} />
        <View style={styles.msgBody}>
          <View style={styles.msgTopRow}>
            <Text style={styles.msgFrom} numberOfLines={1}>
              {msg.from}
            </Text>
            <Meta>{msg.received}</Meta>
          </View>
          <Text style={styles.msgSubject}>{msg.subject}</Text>
          <View style={styles.msgMetaRow}>
            <Pill label={msg.cat} kind={catPill(msg.cat)} />
            {msg.deadline !== "—" ? <Meta>· {msg.deadline}</Meta> : null}
          </View>

          {expanded ? (
            <View style={styles.expanded}>
              <View style={styles.take}>
                <View style={styles.takeHead}>
                  <AlfMark size={12} color={colors.accent} />
                  <Text style={styles.takeLabel}>
                    Alfred's take · {Math.round(msg.confidence * 100)}%
                    confident
                  </Text>
                </View>
                <Text style={styles.takeText}>{msg.summary}</Text>
                <Text style={styles.takeAction}>
                  <Text style={styles.takeActionLabel}>
                    Suggested action —{" "}
                  </Text>
                  {msg.action}
                </Text>
              </View>
              <Text style={styles.preview}>{msg.preview}</Text>
              <View style={styles.msgActions}>
                {msg.cat === "Needs Reply" ? (
                  <Btn
                    label="Draft reply"
                    kind="accent"
                    tiny
                    onPress={onDraft}
                  />
                ) : null}
                {msg.cat === "Needs Decision" ? (
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
  takeAction: {
    fontSize: 12.5,
    color: colors.ink2,
    marginTop: 8,
    fontStyle: "italic",
  },
  takeActionLabel: {
    fontStyle: "normal",
    fontWeight: "500",
    color: colors.ink3,
  },
  preview: {
    fontSize: 13,
    color: colors.ink3,
    lineHeight: 20,
    marginBottom: 12,
  },
  msgActions: { flexDirection: "row", gap: 8, flexWrap: "wrap" },

  zero: { alignItems: "center", paddingVertical: 40, gap: 6 },
});
