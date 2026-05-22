// Capture — full-screen voice/text/photo/forward capture, pixel-matched to the
// prototype's ScreenCapture. Modes (Speak/Type/Snap/Forward); voice idle (breathing
// rings + mic), recording (ink bg, timer, animated waveform), parsed (transcript,
// detected chips, extracted task cards). Type → captureText, Voice → captureVoice
// (both real). Snap/Forward are styled stubs, as in the prototype.

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Animated,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import type { CaptureResponse } from "@albert/shared-types";

import { api } from "@/api/client";
import { useVoiceCapture } from "@/api/useVoiceCapture";
import { Ic, AlfMark } from "@/components/icons";
import {
  Btn,
  Eyebrow,
  IconBtn,
  Meta,
  Pill,
  Serif,
  SerifEm,
  inputPlaceholder,
} from "@/components/ui";
import { colors, fonts, layout } from "@/theme/theme";

type Mode = "voice" | "text" | "photo" | "forward";
type Phase = "idle" | "recording" | "parsed";

const MODES: { id: Mode; label: string }[] = [
  { id: "voice", label: "Speak" },
  { id: "text", label: "Type" },
  { id: "photo", label: "Snap" },
  { id: "forward", label: "Forward" },
];

export function CaptureScreen({ onClose }: { onClose: () => void }) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [mode, setMode] = useState<Mode>("voice");
  const [text, setText] = useState("");
  const [result, setResult] = useState<CaptureResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const voice = useVoiceCapture(async (r) => {
    setResult(r);
    setPhase("parsed");
  });

  const recording = voice.state === "recording";
  const dark = phase === "recording" || recording;

  const submitText = useCallback(async () => {
    const t = text.trim();
    if (!t) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.captureText(t);
      setResult(r);
      setPhase("parsed");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't parse that note");
    } finally {
      setBusy(false);
    }
  }, [text]);

  const reset = () => {
    setPhase("idle");
    setText("");
    setResult(null);
    setError(null);
  };

  return (
    <View style={[styles.screen, dark && styles.screenDark]}>
      {/* Top bar */}
      <View style={styles.top}>
        <IconBtn onPress={onClose} style={dark ? styles.iconDark : undefined}>
          <Ic.Close size={18} color={dark ? colors.paper : colors.ink2} />
        </IconBtn>
        <Eyebrow color={dark ? "rgba(255,255,255,0.6)" : colors.ink3}>
          {phase === "idle"
            ? "New capture"
            : recording
              ? "Listening"
              : "Captured"}
        </Eyebrow>
        <View style={styles.topSpacer} />
      </View>

      {phase === "parsed" && result ? (
        <ParsedState
          result={result}
          transcript={text}
          onRedo={reset}
          onDone={onClose}
        />
      ) : recording ? (
        <RecordingState onStop={() => void voice.stop()} />
      ) : (
        <IdleState
          mode={mode}
          setMode={setMode}
          text={text}
          setText={setText}
          busy={busy}
          error={error}
          onStartVoice={() => void voice.start()}
          onSubmitText={() => void submitText()}
        />
      )}
    </View>
  );
}

// ── Idle ─────────────────────────────────────────────────────────────────────

function IdleState({
  mode,
  setMode,
  text,
  setText,
  busy,
  error,
  onStartVoice,
  onSubmitText,
}: {
  mode: Mode;
  setMode: (m: Mode) => void;
  text: string;
  setText: (t: string) => void;
  busy: boolean;
  error: string | null;
  onStartVoice: () => void;
  onSubmitText: () => void;
}) {
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.idleContent}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.idleTitle}>
        <Serif size={30} style={styles.idleHeading}>
          Tell me what's <SerifEm>on your mind</SerifEm>.
        </Serif>
        <Text style={styles.idleSub}>
          Speak in any order. I'll pull out tasks, dates, people, and projects.
        </Text>
      </View>

      {/* Mode tabs */}
      <View style={styles.modeTabs}>
        {MODES.map((m) => {
          const active = mode === m.id;
          return (
            <Pressable
              key={m.id}
              onPress={() => setMode(m.id)}
              style={[styles.modeTab, active && styles.modeTabActive]}
            >
              <ModeIcon mode={m.id} active={active} />
              <Text
                style={[styles.modeLabel, active && styles.modeLabelActive]}
              >
                {m.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.modeBody}>
        {mode === "voice" ? <VoiceIdle onStart={onStartVoice} /> : null}
        {mode === "text" ? (
          <TextIdle
            text={text}
            setText={setText}
            busy={busy}
            onSubmit={onSubmitText}
          />
        ) : null}
        {mode === "photo" ? <PhotoIdle /> : null}
        {mode === "forward" ? <ForwardIdle /> : null}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {/* I'll listen for */}
      <View style={styles.listenFor}>
        <View style={styles.listenHead}>
          <AlfMark size={12} color={colors.accent} />
          <Text style={styles.listenLabel}>I'll listen for</Text>
        </View>
        <View style={styles.chipRow}>
          {[
            {
              label: "Dates",
              icon: <Ic.Calendar size={11} color={colors.ink3} stroke={1.8} />,
            },
            {
              label: "People",
              icon: <Ic.User size={11} color={colors.ink3} stroke={1.8} />,
            },
            {
              label: "Tasks",
              icon: <Ic.Check size={11} color={colors.ink3} stroke={2.4} />,
            },
            {
              label: "Projects",
              icon: <Ic.Stack size={11} color={colors.ink3} stroke={1.8} />,
            },
            {
              label: "Decisions",
              icon: <Ic.Bell size={11} color={colors.ink3} stroke={1.8} />,
            },
          ].map((c) => (
            <Pill
              key={c.label}
              label={c.label}
              kind="muted"
              mono={false}
              leading={c.icon}
            />
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

function ModeIcon({ mode, active }: { mode: Mode; active: boolean }) {
  const color = active ? colors.ink : colors.ink3;
  if (mode === "voice") return <Ic.Mic size={18} color={color} stroke={1.6} />;
  if (mode === "text") return <Ic.Type size={18} color={color} stroke={1.6} />;
  if (mode === "photo")
    return <Ic.Image size={18} color={color} stroke={1.6} />;
  return <Ic.Forward size={18} color={color} stroke={1.6} />;
}

function VoiceIdle({ onStart }: { onStart: () => void }) {
  const r1 = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(r1, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(r1, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [r1]);
  const scale = r1.interpolate({
    inputRange: [0, 1],
    outputRange: [0.94, 1.06],
  });

  return (
    <View style={styles.voiceIdle}>
      <View style={styles.ringWrap}>
        <Animated.View
          style={[styles.ring, styles.ring1, { transform: [{ scale }] }]}
        />
        <Animated.View
          style={[styles.ring, styles.ring2, { transform: [{ scale }] }]}
        />
        <Pressable
          style={styles.micBtn}
          onPress={onStart}
          accessibilityLabel="Start recording"
        >
          <Ic.Mic size={38} color="#fff" stroke={1.6} />
        </Pressable>
      </View>
      <Serif size={16} italic color={colors.ink2} style={styles.voiceHint}>
        Tap to begin. Take your time.
      </Serif>
      <Meta>Records a voice note, then sorts it into tasks</Meta>
    </View>
  );
}

function TextIdle({
  text,
  setText,
  busy,
  onSubmit,
}: {
  text: string;
  setText: (t: string) => void;
  busy: boolean;
  onSubmit: () => void;
}) {
  return (
    <View style={styles.textIdle}>
      <TextInput
        value={text}
        onChangeText={setText}
        placeholder="e.g. remind me to email Daniel the A3 PDF tomorrow, book the United flight home for Friday morning, ask Chen about the lab write-up tonight…"
        placeholderTextColor={inputPlaceholder}
        multiline
        style={styles.textArea}
      />
      <Btn
        label={busy ? "Parsing…" : "Add to Today"}
        kind="accent"
        full
        disabled={busy || !text.trim()}
        onPress={onSubmit}
      />
    </View>
  );
}

function PhotoIdle() {
  return (
    <View style={styles.dropZone}>
      <View style={styles.dropIcon}>
        <Ic.Image size={26} color={colors.ink3} stroke={1.4} />
      </View>
      <Serif size={17} color={colors.ink2} style={styles.dropTitle}>
        Whiteboard, screenshot, or paper to-do list.
      </Serif>
      <Meta style={styles.dropMeta}>
        I'll read it, extract tasks, and ask before adding anything ambiguous.
      </Meta>
      <Btn
        label="Choose photo"
        kind="ghost"
        tiny
        leading={<Ic.Plus size={11} color={colors.ink2} />}
        onPress={() =>
          Alert.alert(
            "Photo capture",
            "Snapping a whiteboard or to-do list is coming soon. For now, speak or type your note.",
          )
        }
      />
    </View>
  );
}

function ForwardIdle() {
  return (
    <View style={styles.forwardCard}>
      <Text style={styles.forwardLabel}>Forward anything to</Text>
      <View style={styles.forwardAddr}>
        <Ic.Mail size={14} color={colors.ink3} />
        <Text style={styles.forwardEmail}>you@in.albert.app</Text>
        <Btn
          label="Copy"
          kind="ghost"
          tiny
          onPress={() =>
            Alert.alert(
              "Forwarding address",
              "you@in.albert.app — forward email or share notes here and Albert sorts them into tasks. (Clipboard copy coming soon.)",
            )
          }
        />
      </View>
      <Meta style={styles.forwardMeta}>
        Works with email, WhatsApp share, the iOS share sheet, or a pasted link.
        I'll extract tasks and tell you what I found.
      </Meta>
    </View>
  );
}

// ── Recording ──────────────────────────────────────────────────────────────

function RecordingState({ onStop }: { onStop: () => void }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 0.1), 100);
    return () => clearInterval(t);
  }, []);
  return (
    <View style={styles.recording}>
      <View style={styles.recTop}>
        <Text style={styles.recListening}>Listening</Text>
        <Serif size={38} color="#fff" style={styles.recTimer}>
          {elapsed.toFixed(1)}
          <Text style={styles.recTimerUnit}>s</Text>
        </Serif>
      </View>
      <Waveform />
      <Serif
        size={14}
        italic
        color="rgba(255,255,255,0.7)"
        style={styles.recHint}
      >
        Take your time. I'll sort dates, people, and projects when you stop.
      </Serif>
      <Pressable
        style={styles.stopBtn}
        onPress={onStop}
        accessibilityLabel="Stop"
      >
        <View style={styles.stopSquare} />
      </Pressable>
    </View>
  );
}

function Waveform() {
  const bars = useRef(
    Array.from({ length: 32 }, () => new Animated.Value(0.3)),
  ).current;
  useEffect(() => {
    const loops = bars.map((b, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(b, {
            toValue: 1,
            duration: 400 + (i % 5) * 90,
            useNativeDriver: false,
          }),
          Animated.timing(b, {
            toValue: 0.25,
            duration: 400 + (i % 7) * 80,
            useNativeDriver: false,
          }),
        ]),
      ),
    );
    loops.forEach((l, i) => setTimeout(() => l.start(), i * 30));
    return () => loops.forEach((l) => l.stop());
  }, [bars]);

  return (
    <View style={styles.waveform}>
      {bars.map((b, i) => (
        <Animated.View
          key={i}
          style={[
            styles.waveBar,
            {
              height: b.interpolate({
                inputRange: [0, 1],
                outputRange: [6, 56],
              }),
              opacity: b.interpolate({
                inputRange: [0, 1],
                outputRange: [0.5, 1],
              }),
            },
          ]}
        />
      ))}
    </View>
  );
}

// ── Parsed ───────────────────────────────────────────────────────────────────

function ParsedState({
  result,
  transcript,
  onRedo,
  onDone,
}: {
  result: CaptureResponse;
  transcript: string;
  onRedo: () => void;
  onDone: () => void;
}) {
  const tasks = result.tasks;
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.parsedContent}
    >
      <Serif size={26} style={styles.parsedHeading}>
        Here's what I <SerifEm>heard</SerifEm>.
      </Serif>

      {transcript ? (
        <View style={styles.transcript}>
          <Text style={styles.transcriptLabel}>Transcript</Text>
          <Serif
            size={15.5}
            italic
            color={colors.ink2}
            style={styles.transcriptText}
          >
            "{transcript}"
          </Serif>
        </View>
      ) : null}

      {result.detected_project ? (
        <View style={styles.chips}>
          <Pill
            label={result.detected_project}
            kind="accent"
            leading={<Ic.Stack size={9} color={colors.accentInk} stroke={2} />}
          />
        </View>
      ) : null}

      <Text style={styles.parsedSection}>
        {tasks.length} task{tasks.length === 1 ? "" : "s"} extracted
      </Text>
      <View style={styles.taskList}>
        {tasks.map((t, i) => (
          <View key={t.id} style={styles.taskCard}>
            <View style={styles.taskNum}>
              <Text style={styles.taskNumText}>{i + 1}</Text>
            </View>
            <View style={styles.taskBody}>
              <Text style={styles.taskTitle}>{t.title}</Text>
              <View style={styles.taskMeta}>
                {t.due_date ? <Pill label={t.due_date} kind="warn" /> : null}
              </View>
            </View>
          </View>
        ))}
      </View>

      <View style={styles.parsedActions}>
        <Btn
          label="Redo"
          kind="ghost"
          onPress={onRedo}
          style={styles.redoBtn}
          leading={<Ic.Refresh size={12} color={colors.ink2} />}
        />
        <Btn
          label={`Add ${tasks.length} to Today`}
          kind="accent"
          onPress={onDone}
          style={styles.addBtn}
          leading={<Ic.Check size={12} color="#fff" stroke={2.4} />}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  screenDark: { backgroundColor: colors.ink },
  top: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: layout.padX,
    paddingTop: layout.topPad,
    paddingBottom: 8,
  },
  iconDark: {
    backgroundColor: "rgba(255,255,255,0.08)",
    borderColor: "rgba(255,255,255,0.18)",
  },
  topSpacer: { width: 36 },
  scroll: { flex: 1 },

  idleContent: { paddingHorizontal: layout.padX, paddingBottom: 24 },
  idleTitle: { paddingVertical: 16 },
  idleHeading: { maxWidth: 300, lineHeight: 32 },
  idleSub: { color: colors.ink3, marginTop: 8, fontSize: 14, lineHeight: 21 },

  modeTabs: {
    flexDirection: "row",
    gap: 4,
    padding: 4,
    backgroundColor: colors.paper2,
    borderRadius: 14,
  },
  modeTab: {
    flex: 1,
    alignItems: "center",
    gap: 4,
    paddingVertical: 8,
    borderRadius: 11,
  },
  modeTabActive: {
    backgroundColor: colors.card,
    shadowColor: "#19171A",
    shadowOpacity: 0.06,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },
  modeLabel: {
    fontFamily: fonts.mono,
    fontSize: 11,
    textTransform: "uppercase",
    color: colors.ink3,
  },
  modeLabelActive: { color: colors.ink },
  modeBody: { marginTop: 18, minHeight: 220 },

  voiceIdle: { alignItems: "center", paddingVertical: 24, gap: 6 },
  ringWrap: {
    width: 200,
    height: 200,
    alignItems: "center",
    justifyContent: "center",
  },
  ring: { position: "absolute", borderRadius: 100 },
  ring1: { width: 200, height: 200, backgroundColor: "rgba(58,93,168,0.08)" },
  ring2: { width: 152, height: 152, backgroundColor: "rgba(58,93,168,0.12)" },
  micBtn: {
    width: 116,
    height: 116,
    borderRadius: 58,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.accent,
    shadowOpacity: 0.32,
    shadowRadius: 36,
    shadowOffset: { width: 0, height: 14 },
  },
  voiceHint: { marginTop: 18 },

  textIdle: { gap: 10 },
  textArea: {
    minHeight: 180,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    borderRadius: 16,
    padding: 14,
    backgroundColor: colors.card,
    color: colors.ink,
    fontSize: 15,
    lineHeight: 23,
    textAlignVertical: "top",
  },

  dropZone: {
    borderWidth: 1.5,
    borderStyle: "dashed",
    borderColor: colors.hair2,
    borderRadius: 16,
    padding: 28,
    alignItems: "center",
    gap: 10,
    backgroundColor: colors.paper2,
    minHeight: 180,
    justifyContent: "center",
  },
  dropIcon: {
    width: 54,
    height: 54,
    borderRadius: 14,
    backgroundColor: colors.card,
    alignItems: "center",
    justifyContent: "center",
  },
  dropTitle: { textAlign: "center", lineHeight: 23 },
  dropMeta: { maxWidth: 240, textAlign: "center", lineHeight: 18 },

  forwardCard: {
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    borderRadius: 16,
    padding: 16,
  },
  forwardLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
    marginBottom: 8,
  },
  forwardAddr: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colors.paper2,
    borderRadius: 10,
  },
  forwardEmail: {
    flex: 1,
    fontFamily: fonts.mono,
    fontSize: 13,
    color: colors.ink,
  },
  forwardMeta: { marginTop: 10, lineHeight: 18 },

  error: { color: colors.warn, fontSize: 13, marginTop: 12 },

  listenFor: {
    marginTop: 18,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
  },
  listenHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 10,
  },
  listenLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
  },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },

  recording: {
    flex: 1,
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: layout.padX,
    paddingVertical: 40,
  },
  recTop: { alignItems: "center", marginTop: 20, gap: 12 },
  recListening: {
    fontFamily: fonts.mono,
    fontSize: 11,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: "rgba(255,255,255,0.55)",
  },
  recTimer: { letterSpacing: -0.4 },
  recTimerUnit: { color: "rgba(255,255,255,0.4)" },
  recHint: { textAlign: "center", maxWidth: 260, lineHeight: 21 },
  waveform: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    height: 80,
  },
  waveBar: { width: 3, borderRadius: 100, backgroundColor: "#8aa0cf" },
  stopBtn: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.4,
    shadowRadius: 40,
    shadowOffset: { width: 0, height: 12 },
  },
  stopSquare: {
    width: 28,
    height: 28,
    borderRadius: 6,
    backgroundColor: colors.accent,
  },

  parsedContent: { paddingHorizontal: layout.padX, paddingBottom: 30 },
  parsedHeading: { marginTop: 8 },
  transcript: {
    marginTop: 14,
    backgroundColor: colors.paper2,
    borderRadius: 18,
    padding: layout.cardPad,
  },
  transcriptLabel: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: colors.ink4,
    marginBottom: 8,
  },
  transcriptText: { lineHeight: 23 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 14 },
  parsedSection: {
    fontSize: 13,
    fontWeight: "500",
    letterSpacing: 0.78,
    textTransform: "uppercase",
    color: colors.ink3,
    marginTop: 22,
    marginBottom: 8,
  },
  taskList: { gap: 8 },
  taskCard: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    backgroundColor: colors.card,
    borderRadius: 18,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    padding: 14,
  },
  taskNum: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.accentSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  taskNumText: {
    fontFamily: fonts.mono,
    fontSize: 11,
    color: colors.accentInk,
  },
  taskBody: { flex: 1, minWidth: 0 },
  taskTitle: { fontSize: 15, lineHeight: 20, color: colors.ink },
  taskMeta: {
    flexDirection: "row",
    gap: 6,
    marginTop: 6,
    alignItems: "center",
  },
  parsedActions: { flexDirection: "row", gap: 8, marginTop: 20 },
  redoBtn: { flex: 1 },
  addBtn: { flex: 2 },
});
