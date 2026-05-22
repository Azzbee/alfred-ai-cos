// Shared UI primitives for Albert's editorial light theme, ported 1:1 from the
// Alfred prototype's CSS classes (alf-serif, alf-eyebrow, alf-h2/h3, alf-pill,
// alf-card, alf-card-flat, alf-btn, alf-check, alf-icon-btn, Avatar). See
// theme/DESIGN.md for the spec. Plain RN primitives + react-native-svg icons.

import { useEffect, useRef, type ReactNode } from "react";
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from "react-native";

import { avatarTone, initials } from "@/lib/avatar";
import { colors, fonts, layout, radius, spacing } from "@/theme/theme";

// ── Text ──────────────────────────────────────────────────────────────────

// Serif display text (greetings, titles, priority titles). Italic optional.
// `em` portions of a title are italic + accentInk; use <SerifEm> inline.
export function Serif({
  children,
  size = 18,
  color = colors.ink,
  italic = false,
  style,
}: {
  children: ReactNode;
  size?: number;
  color?: string;
  italic?: boolean;
  style?: StyleProp<TextStyle>;
}) {
  return (
    <Text
      style={[
        {
          fontFamily: fonts.serif,
          fontSize: size,
          lineHeight: size * 1.15,
          letterSpacing: -0.01 * size,
          color,
          fontStyle: italic ? "italic" : "normal",
        },
        style,
      ]}
    >
      {children}
    </Text>
  );
}

// Inline italic accent span inside a serif title ("Good morning, <em>Maya</em>.").
export function SerifEm({ children }: { children: ReactNode }) {
  return (
    <Text style={{ fontStyle: "italic", color: colors.accentInk }}>
      {children}
    </Text>
  );
}

// alf-h2: serif 22, used in sheet headers.
export function H2({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<TextStyle>;
}) {
  return <Text style={[styles.h2, style]}>{children}</Text>;
}

// Mono uppercase eyebrow ("TUESDAY · MAY 19").
export function Eyebrow({
  children,
  color = colors.ink3,
  style,
}: {
  children: ReactNode;
  color?: string;
  style?: StyleProp<TextStyle>;
}) {
  return <Text style={[styles.eyebrow, { color }, style]}>{children}</Text>;
}

// alf-h3: uppercase sans section header with an optional right-aligned slot.
export function SectionTitle({
  label,
  right,
  style,
}: {
  label: string;
  right?: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.sectionRow, style]}>
      <Text style={styles.sectionLabel}>{label}</Text>
      {right ?? null}
    </View>
  );
}

// alf-meta: mono 12, ink3.
export function Meta({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<TextStyle>;
}) {
  return <Text style={[styles.meta, style]}>{children}</Text>;
}

// Editorial screen header used by the inner screens: mono eyebrow + serif title.
export function ScreenHeader({
  eyebrow,
  title,
  titleEm,
  subtitle,
  titleSize = 34,
  right,
}: {
  eyebrow: string;
  title: ReactNode;
  titleEm?: string;
  subtitle?: string;
  titleSize?: number;
  right?: ReactNode;
}) {
  return (
    <View style={styles.screenHeader}>
      <View style={styles.screenHeaderRow}>
        <Eyebrow>{eyebrow}</Eyebrow>
        {right ?? null}
      </View>
      <Serif size={titleSize} style={styles.screenTitle}>
        {title}
        {titleEm ? <SerifEm>{titleEm}</SerifEm> : null}
      </Serif>
      {subtitle ? <Text style={styles.screenSubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

// ── Pills ─────────────────────────────────────────────────────────────────

type PillKind = "accent" | "warn" | "muted";

export function Pill({
  label,
  kind = "muted",
  dot = false,
  mono = true,
  leading,
  onPress,
  style,
}: {
  label: ReactNode;
  kind?: PillKind;
  dot?: boolean;
  mono?: boolean; // false → sans, no uppercase (inbox cats, "I'll listen for")
  leading?: ReactNode;
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const textColor = PILL_TEXT[kind];
  const body = (
    <View style={[styles.pill, styles[`pill_${kind}`], style]}>
      {dot ? (
        <View style={[styles.pillDot, { backgroundColor: textColor }]} />
      ) : null}
      {leading ?? null}
      <Text
        style={[
          mono ? styles.pillTextMono : styles.pillTextSans,
          { color: textColor },
        ]}
      >
        {label}
      </Text>
    </View>
  );
  return onPress ? (
    <Pressable
      hitSlop={6}
      onPress={onPress}
      style={({ pressed }) => (pressed ? styles.pressedSoft : null)}
    >
      {body}
    </Pressable>
  ) : (
    body
  );
}

const PILL_TEXT: Record<PillKind, string> = {
  accent: colors.accentInk,
  warn: colors.warn,
  muted: colors.ink3,
};

// ── Cards ─────────────────────────────────────────────────────────────────

export function Card({
  children,
  flat = false,
  style,
  onPress,
}: {
  children: ReactNode;
  flat?: boolean;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
}) {
  const body = (
    <View style={[flat ? styles.cardFlat : styles.card, style]}>
      {children}
    </View>
  );
  return onPress ? (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => (pressed ? styles.pressedSoft : null)}
    >
      {body}
    </Pressable>
  ) : (
    body
  );
}

// ── Buttons ───────────────────────────────────────────────────────────────

type BtnKind = "ink" | "accent" | "ghost";

export function Btn({
  label,
  onPress,
  kind = "ink",
  tiny = false,
  full = false,
  disabled = false,
  leading,
  style,
}: {
  label: ReactNode;
  onPress?: () => void;
  kind?: BtnKind;
  tiny?: boolean;
  full?: boolean;
  disabled?: boolean;
  leading?: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.btn,
        styles[`btn_${kind}`],
        tiny && styles.btnTiny,
        full && styles.btnFull,
        disabled && styles.btnDisabled,
        pressed && !disabled && styles.btnPressed,
        style,
      ]}
      onPress={onPress}
      disabled={disabled}
    >
      {leading ?? null}
      <Text
        style={[
          styles.btnText,
          styles[`btnText_${kind}`],
          tiny && styles.btnTextTiny,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

// alf-icon-btn: 36px circle, card bg, hair2 border, soft shadow.
export function IconBtn({
  children,
  onPress,
  style,
}: {
  children: ReactNode;
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.iconBtn,
        pressed && styles.pressedSoft,
        style,
      ]}
      onPress={onPress}
    >
      {children}
    </Pressable>
  );
}

// ── Check ─────────────────────────────────────────────────────────────────

// Circular checkbox. Tapping animates an accent fill scaling in from the center with
// the white tick popping over it (the prototype's `transition: all .15s`). The whole
// control dips on press for tactile feedback.
export function Check({
  done,
  onPress,
  style,
}: {
  done: boolean;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const fill = useRef(new Animated.Value(done ? 1 : 0)).current;
  const press = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.spring(fill, {
      toValue: done ? 1 : 0,
      useNativeDriver: true,
      friction: 6,
      tension: 140,
    }).start();
  }, [done, fill]);

  const dip = () =>
    Animated.spring(press, {
      toValue: 0.85,
      useNativeDriver: true,
      speed: 50,
    }).start();
  const lift = () =>
    Animated.spring(press, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
    }).start();

  return (
    <Pressable
      hitSlop={8}
      onPress={onPress}
      onPressIn={dip}
      onPressOut={lift}
      style={style}
    >
      <Animated.View style={[styles.check, { transform: [{ scale: press }] }]}>
        <Animated.View
          style={[
            styles.checkFill,
            { opacity: fill, transform: [{ scale: fill }] },
          ]}
        />
        <Animated.Text style={[styles.checkMark, { opacity: fill }]}>
          ✓
        </Animated.Text>
      </Animated.View>
    </Pressable>
  );
}

// ── Avatar ────────────────────────────────────────────────────────────────

// Deterministic avatar from a person's name: initials + a stable tone color.
// The pure logic lives in lib/avatar (imported above) so it can be unit-tested
// without RN; re-exported here for components that import from @/components/ui.
export { avatarTone, initials };

export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: avatarTone(name),
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Text
        style={{
          color: "#fff",
          fontSize: size * 0.36,
          fontWeight: "600",
          letterSpacing: 0.5,
        }}
      >
        {initials(name)}
      </Text>
    </View>
  );
}

// ── Misc ──────────────────────────────────────────────────────────────────

// FooterStamp: the quiet sync line at the bottom of feed screens.
export function FooterStamp({ text }: { text?: string }) {
  return (
    <View style={styles.footerStamp}>
      <Text style={styles.footerStampText}>
        {text ?? "Gmail synced just now · Calendar just now"}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  h2: {
    fontFamily: fonts.serif,
    fontSize: 22,
    letterSpacing: -0.22,
    lineHeight: 25,
    color: colors.ink,
  },
  eyebrow: {
    fontFamily: fonts.mono,
    fontSize: 11,
    letterSpacing: 1.4,
    textTransform: "uppercase",
  },
  sectionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: layout.gapSection,
    marginBottom: 10,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "500",
    letterSpacing: 0.78,
    textTransform: "uppercase",
    color: colors.ink3,
  },
  meta: { fontFamily: fonts.mono, fontSize: 12, color: colors.ink3 },

  screenHeader: { gap: spacing.xs, marginBottom: spacing.sm },
  screenHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  screenTitle: { marginTop: 2 },
  screenSubtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: colors.ink3,
    marginTop: spacing.xs,
    maxWidth: 320,
  },

  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
    borderWidth: StyleSheet.hairlineWidth,
    alignSelf: "flex-start",
  },
  pillDot: { width: 5, height: 5, borderRadius: 2.5 },
  pillTextMono: {
    fontFamily: fonts.mono,
    fontSize: 10.5,
    letterSpacing: 0.4,
    textTransform: "uppercase",
  },
  pillTextSans: { fontSize: 12.5 },
  pill_accent: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
  },
  pill_warn: { backgroundColor: colors.warnSoft, borderColor: colors.warn },
  pill_muted: { backgroundColor: "transparent", borderColor: colors.hair2 },

  card: {
    backgroundColor: colors.card,
    borderRadius: radius.card,
    padding: layout.cardPad,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair,
    shadowColor: "#19171A",
    shadowOpacity: 0.04,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },
  cardFlat: {
    backgroundColor: "transparent",
    borderRadius: 14,
    padding: layout.cardPad,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
  },

  btn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderRadius: radius.pill,
    paddingVertical: 10,
    paddingHorizontal: spacing.md,
  },
  btnTiny: { paddingVertical: 6, paddingHorizontal: 10 },
  btnFull: { width: "100%" },
  btn_ink: { backgroundColor: colors.ink },
  btn_accent: { backgroundColor: colors.accent },
  btn_ghost: {
    backgroundColor: "transparent",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
  },
  btnDisabled: { opacity: 0.4 },
  btnPressed: { transform: [{ scale: 0.97 }] },
  btnText: { fontSize: 14, fontWeight: "500" },
  btnTextTiny: { fontSize: 12 },
  btnText_ink: { color: colors.paper },
  btnText_accent: { color: "#FFFFFF" },
  btnText_ghost: { color: colors.ink2 },

  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    shadowColor: "#19171A",
    shadowOpacity: 0.04,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },

  check: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.2,
    borderColor: colors.ink4,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  // Accent fill that scales in from the center when done. Inset by -1.2 so it covers
  // the ink4 ring, giving the prototype's solid accent disc on completion.
  checkFill: {
    position: "absolute",
    top: -1.2,
    left: -1.2,
    right: -1.2,
    bottom: -1.2,
    borderRadius: 11,
    backgroundColor: colors.accent,
  },
  checkMark: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 15,
  },

  // Shared press feedback for tappable cards / pills / icon buttons.
  pressedSoft: { opacity: 0.6 },

  footerStamp: { marginTop: 28, paddingVertical: 14, alignItems: "center" },
  footerStampText: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: colors.ink4,
  },
});

// Shared text-input styling for the editorial theme.
export const inputStyle = {
  backgroundColor: colors.card,
  borderWidth: StyleSheet.hairlineWidth,
  borderColor: colors.hair2,
  borderRadius: radius.sm,
  paddingHorizontal: spacing.md,
  paddingVertical: 11,
  fontSize: 15,
  color: colors.ink,
} as const;

export const inputPlaceholder = colors.ink4;
