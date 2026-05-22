// Ask Alfred — chat screen, pixel-matched to the prototype's ScreenAsk. Serif title,
// chat bubbles (Alfred serif/left, user ink-pill/right), suggested questions, composer
// with an accent send button. Runs on the scripted reply engine (src/data/demo.ts)
// until a real chat backend exists; the bubble/composer UI is final.

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
import { useRouter } from "expo-router";

import {
  CHAT_SEED,
  SUGGESTED_QUESTIONS,
  scriptedReply,
  type ChatMessage,
} from "@/data/demo";
import { ApprovalSheet } from "@/screens/sheets/ApprovalSheet";
import { MeetingPrepSheet } from "@/screens/sheets/MeetingPrepSheet";
import { Ic, AlfMark } from "@/components/icons";
import { useShell } from "@/components/Shell";
import {
  Btn,
  Eyebrow,
  Serif,
  SerifEm,
  inputPlaceholder,
} from "@/components/ui";
import { colors, fonts, layout, radius, spacing } from "@/theme/theme";

export function AskScreen() {
  const router = useRouter();
  const { openSheet, showToast } = useShell();
  const [chat, setChat] = useState<ChatMessage[]>(CHAT_SEED);
  const [input, setInput] = useState("");
  const scrollRef = useRef<ScrollView>(null);

  const handleAction = useCallback(
    (kind: "today" | "meeting" | "approval") => {
      if (kind === "today") router.navigate("/(tabs)");
      else if (kind === "approval")
        openSheet(<ApprovalSheet onDone={() => showToast("Sent.")} />);
      else if (kind === "meeting")
        openSheet(<MeetingPrepSheet eventId="demo" />);
    },
    [router, openSheet, showToast],
  );

  const send = useCallback((text: string) => {
    const q = text.trim();
    if (!q) return;
    setChat((c) => [...c, { role: "user", text: q, ts: "now" }]);
    setInput("");
    setTimeout(() => {
      setChat((c) => [...c, scriptedReply(q)]);
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 600);
  }, []);

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.header}>
        <Eyebrow>Ask Alfred</Eyebrow>
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
          <Bubble key={i} msg={m} onAction={handleAction} />
        ))}
        {chat.length <= 1 ? (
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

      <View style={styles.composer}>
        <View style={styles.composerInner}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Ask Alfred anything…"
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

function Bubble({
  msg,
  onAction,
}: {
  msg: ChatMessage;
  onAction: (kind: "today" | "meeting" | "approval") => void;
}) {
  const isAlf = msg.role === "alfred";
  return (
    <View style={[styles.bubbleWrap, isAlf ? styles.left : styles.right]}>
      {isAlf ? (
        <View style={styles.alfHead}>
          <AlfMark size={22} filled color={colors.accent} />
          <Text style={styles.alfLabel}>Alfred · {msg.ts}</Text>
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
      {msg.actions ? (
        <View style={styles.actions}>
          {msg.actions.map((a, i) => (
            <Btn
              key={i}
              label={a.label}
              kind="ghost"
              tiny
              onPress={() => onAction(a.kind)}
              leading={<Ic.Arrow size={11} color={colors.ink2} />}
            />
          ))}
        </View>
      ) : null}
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
  actions: { flexDirection: "row", gap: 8, marginTop: 10, flexWrap: "wrap" },

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
