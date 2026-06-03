// Ask Albert — chat screen, pixel-matched to the prototype's ScreenAsk. Serif title,
// chat bubbles (Albert serif/left, user ink-pill/right), suggested questions, composer.
// Wired to POST /assistant/ask: it interprets the request and books real calendar time
// ("book my calendar tomorrow 5-6pm"). Non-calendar requests get an honest reply.

import { useCallback, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api } from "@/api/client";
import { CompanionAvatar } from "@/components/CompanionAvatar";
import { useCompanionAvatar } from "@/context/CompanionAvatarContext";
import { CHAT_SEED, SUGGESTED_QUESTIONS, type ChatMessage } from "@/data/demo";
import { Ic, AlfMark } from "@/components/icons";
import { useShell } from "@/components/Shell";
import { Eyebrow, Serif, SerifEm, inputPlaceholder } from "@/components/ui";
import { colors, fonts, layout } from "@/theme/theme";

export function AskScreen() {
  const { showToast } = useShell();
  const { meta, state, setThinking, recordEvent } = useCompanionAvatar();
  const [chat, setChat] = useState<ChatMessage[]>(CHAT_SEED);
  const [input, setInput] = useState("");
  const [thinking, setThinkingLocal] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  // Mirror local thinking flag into companion context so the avatar animates + mood updates.
  const setThinkingBoth = useCallback(
    (v: boolean) => {
      setThinkingLocal(v);
      setThinking(v);
    },
    [setThinking],
  );

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || thinking) return;
      setChat((c) => [...c, { role: "user", text: q, ts: "now" }]);
      setInput("");
      setThinkingBoth(true);
      scrollRef.current?.scrollToEnd({ animated: true });
      try {
        const res = await api.ask(q);
        setChat((c) => [...c, { role: "alfred", text: res.reply, ts: "now" }]);
        if (res.action === "booked") showToast("Added to your calendar.");
        // Grant companion XP for each assistant message (capped daily in agentMeta).
        void recordEvent("agent_message_sent");
      } catch (e) {
        setChat((c) => [
          ...c,
          {
            role: "alfred",
            text:
              e instanceof Error
                ? `Something went wrong: ${e.message}`
                : "Something went wrong.",
            ts: "now",
          },
        ]);
      } finally {
        setThinkingBoth(false);
        scrollRef.current?.scrollToEnd({ animated: true });
      }
    },
    [thinking, showToast, setThinkingBoth, recordEvent],
  );

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.header}>
        <Eyebrow>Ask Albert</Eyebrow>
        <Serif size={30} style={styles.title}>
          What's on your <SerifEm>mind?</SerifEm>
        </Serif>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() =>
          scrollRef.current?.scrollToEnd({ animated: true })
        }
      >
        {chat.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}
        {thinking ? (
          <View style={[styles.bubbleWrap, styles.left]}>
            <View style={styles.alfHead}>
              <AlfMark size={22} filled color={colors.accent} />
              <Text style={styles.alfLabel}>Albert · thinking…</Text>
            </View>
          </View>
        ) : null}
        {chat.length <= 1 && !thinking ? (
          <View style={styles.suggest}>
            <Text style={styles.suggestLabel}>Try asking</Text>
            <View style={styles.suggestList}>
              {SUGGESTED_QUESTIONS.map((q) => (
                <Pressable
                  key={q}
                  style={styles.suggestItem}
                  onPress={() => send(q)}
                >
                  <Serif size={14} italic color={colors.ink2}>
                    "{q}"
                  </Serif>
                  <Ic.Arrow size={14} color={colors.ink4} />
                </Pressable>
              ))}
            </View>
          </View>
        ) : null}
      </ScrollView>

      {/* Companion avatar dock — bottom-right above composer while chatting with Alfred. */}
      <View style={styles.companionDock} pointerEvents="box-none">
        <CompanionAvatar
          size={48}
          level={meta.level}
          color={meta.color}
          state={state}
          compact
        />
      </View>

      <View style={styles.composer}>
        <View style={styles.composerInner}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Ask Albert anything…"
            placeholderTextColor={inputPlaceholder}
            style={styles.composerInput}
            multiline
            onSubmitEditing={() => send(input)}
          />
          <Pressable
            style={styles.sendBtn}
            onPress={() => send(input)}
            accessibilityLabel="Send"
          >
            <Ic.ArrowUp size={16} color="#fff" stroke={2} />
          </Pressable>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

function Bubble({ msg }: { msg: ChatMessage }) {
  const isAlf = msg.role === "alfred";
  return (
    <View style={[styles.bubbleWrap, isAlf ? styles.left : styles.right]}>
      {isAlf ? (
        <View style={styles.alfHead}>
          <AlfMark size={22} filled color={colors.accent} />
          <Text style={styles.alfLabel}>Albert · {msg.ts}</Text>
        </View>
      ) : null}
      {isAlf ? (
        <Serif size={17} style={styles.alfText}>
          {msg.text}
        </Serif>
      ) : (
        <View style={styles.userBubble}>
          <Text style={styles.userText}>{msg.text}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  header: { paddingHorizontal: layout.padX, paddingTop: layout.topPad, gap: 6 },
  title: { marginTop: 2 },
  scroll: { flex: 1 },
  scrollContent: { padding: layout.padX, paddingTop: 12 },

  suggest: { marginTop: 4 },
  suggestLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
    marginBottom: 10,
  },
  suggestList: { gap: 6 },
  suggestItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
  },

  bubbleWrap: { marginBottom: 14, maxWidth: "88%" },
  left: { alignSelf: "flex-start", alignItems: "flex-start" },
  right: { alignSelf: "flex-end", alignItems: "flex-end" },
  alfHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 6,
  },
  alfLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink3,
  },
  alfText: { lineHeight: 25 },
  userBubble: {
    backgroundColor: colors.ink,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 18,
  },
  userText: { color: colors.paper, fontSize: 14.5, lineHeight: 21 },

  // Floating companion — matches prototype annotation (bottom-right of chat area).
  companionDock: {
    position: "absolute",
    right: layout.padX,
    bottom: 72,
    zIndex: 2,
  },

  composer: {
    paddingHorizontal: layout.padX,
    paddingTop: 8,
    paddingBottom: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
    backgroundColor: colors.paper,
  },
  composerInner: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    backgroundColor: colors.card,
    borderRadius: 22,
    paddingVertical: 6,
    paddingLeft: 14,
    paddingRight: 6,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
  },
  composerInput: {
    flex: 1,
    fontSize: 15,
    color: colors.ink,
    maxHeight: 100,
    paddingVertical: 6,
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
});
