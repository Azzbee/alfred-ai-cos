// Alfred's companion avatar — placeholder visual until Lottie animations ship.
//
// Design reference: Alfred-MVP evo-core-lv1.svg (concentric cloud orb with accent
// glow). This component renders that orb with react-native-svg and optional speech
// bubble / mood face text. When Lottie is wired up, swap CloudCoreOrb for a Lottie
// view driven by EVOLUTION_STATES segments from avatarEvolution.ts.
//
// Placements (controlled by parent screens):
//   • today  — top-right greeting chip ("Hi!")
//   • ask    — bottom-right while chatting
//   • home   — inside the center + tab button

import { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import Svg, { Circle, Defs, RadialGradient, Stop } from "react-native-svg";

import {
  AVATAR_STATE_FACE,
  getFormByLevel,
  getLevelFx,
  type AvatarState,
} from "@/lib/agentMeta";
import { colors, fonts } from "@/theme/theme";

export type CompanionAvatarProps = {
  /** Diameter of the orb in logical pixels. */
  size?: number;
  /** Agent level — selects evolution form styling (lv1 / lv5 / lv10 rings). */
  level?: number;
  /** Theme tint for glow; defaults to accent blue. */
  color?: string;
  /** Current mood — affects face glyph and subtle pulse animation. */
  state?: AvatarState;
  /** Optional speech bubble text (e.g. "Hi!" on Today). */
  speech?: string;
  /** When true, hides the mood face label (cleaner in the Ask dock). */
  compact?: boolean;
  /** Called when the user taps the avatar (future: open growth hub). */
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
  /** Accessibility label override. */
  accessibilityLabel?: string;
};

/**
 * Floating companion avatar: orb + optional speech bubble.
 * Wrap in a positioned parent (absolute top-right, bottom-right, etc.).
 */
export function CompanionAvatar({
  size = 56,
  level = 1,
  color = colors.accent,
  state = "idle",
  speech,
  compact = false,
  onPress,
  style,
  accessibilityLabel = "Alfred companion avatar",
}: CompanionAvatarProps) {
  const levelFx = getLevelFx(level);
  const form = getFormByLevel(level);
  const face = AVATAR_STATE_FACE[state];

  // Gentle "breathing" scale — stronger while thinking (matches web AgentAvatarCard).
  const breath = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    const toValue = state === "thinking" ? 1.06 : 1.03;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breath, {
          toValue,
          duration: state === "thinking" ? 1100 : 1400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(breath, {
          toValue: 1,
          duration: state === "thinking" ? 1100 : 1400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [breath, state]);

  const scaledSize = size * levelFx.scale;
  const ringCount = level >= 10 ? 3 : level >= 5 ? 2 : 1;

  const body = (
    <View style={[styles.wrap, style]} accessibilityLabel={accessibilityLabel}>
      {/* Speech bubble sits to the left of the orb on Today header. */}
      {speech ? (
        <View style={styles.bubble}>
          <Text style={styles.bubbleText}>{speech}</Text>
          <View style={styles.bubbleTail} />
        </View>
      ) : null}

      <Animated.View
        style={{
          transform: [{ scale: breath }],
          shadowColor: color,
          shadowOpacity: levelFx.glowAlpha,
          shadowRadius: levelFx.glowBlur * 0.35,
          shadowOffset: { width: 0, height: 4 },
        }}
      >
        <CloudCoreOrb
          size={scaledSize}
          color={color}
          ringCount={ringCount}
          state={state}
        />
      </Animated.View>

      {/* Tiny mood face under the orb — hidden in compact mode (Ask dock). */}
      {!compact ? (
        <Text style={styles.face} numberOfLines={1}>
          {face}
        </Text>
      ) : null}
      {/* Hidden form name for screen readers / dev sanity while assets are stubbed. */}
      <Text style={styles.srOnly}>{form.name}</Text>
    </View>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        style={({ pressed }) => (pressed ? styles.pressed : undefined)}
      >
        {body}
      </Pressable>
    );
  }

  return body;
}

/** SVG cloud-core orb — visual stand-in for evo-core-lv*.svg + future Lottie. */
function CloudCoreOrb({
  size,
  color,
  ringCount,
  state,
}: {
  size: number;
  color: string;
  ringCount: number;
  state: AvatarState;
}) {
  // Thinking state gets a dashed outer ring (evo-core-lv1 pattern).
  const outerDash = state === "thinking" ? "4 6" : undefined;
  const outerOpacity = state === "sleep" ? 0.35 : 0.55;

  return (
    <Svg width={size} height={size} viewBox="0 0 240 240">
      <Defs>
        <RadialGradient
          id="companionBg"
          cx="120"
          cy="126"
          rx="92"
          ry="92"
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset="0" stopColor={color} stopOpacity="0.35" />
          <Stop offset="1" stopColor={color} stopOpacity="0.08" />
        </RadialGradient>
      </Defs>

      {/* Soft radial fill */}
      <Circle cx="120" cy="120" r="82" fill="url(#companionBg)" />

      {/* Outermost ring — dashed at lv1+, solid when evolved */}
      {ringCount >= 1 ? (
        <Circle
          cx="120"
          cy="120"
          r="74"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={outerDash}
          strokeOpacity={outerOpacity}
          fill="none"
        />
      ) : null}

      {/* Mid ring — appears at lv5+ */}
      {ringCount >= 2 ? (
        <Circle
          cx="120"
          cy="120"
          r="64"
          stroke={color}
          strokeWidth="2.5"
          strokeOpacity="0.65"
          fill="none"
        />
      ) : null}

      {/* Inner ring — appears at lv10 */}
      {ringCount >= 3 ? (
        <Circle
          cx="120"
          cy="120"
          r="54"
          stroke={color}
          strokeWidth="2"
          strokeOpacity="0.85"
          fill="none"
        />
      ) : null}

      {/* Core dot */}
      <Circle
        cx="120"
        cy="120"
        r={state === "success" ? 12 : 8}
        fill={color}
        opacity={state === "sleep" ? 0.5 : 1}
      />
    </Svg>
  );
}

/** Compact orb for the tab bar "home" slot — no face label, fits inside the + circle. */
export function CompanionAvatarHome({
  size = 28,
  level = 1,
  color = colors.accent,
  state = "idle",
}: Pick<CompanionAvatarProps, "size" | "level" | "color" | "state">) {
  const levelFx = getLevelFx(level);
  const ringCount = level >= 10 ? 3 : level >= 5 ? 2 : 1;

  return (
    <View
      style={{
        width: size,
        height: size,
        alignItems: "center",
        justifyContent: "center",
        transform: [{ scale: levelFx.scale * 0.92 }],
      }}
      accessibilityLabel="Alfred companion home"
    >
      <CloudCoreOrb
        size={size}
        color={color}
        ringCount={ringCount}
        state={state}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: "relative",
    alignItems: "center",
    gap: 2,
  },
  pressed: { opacity: 0.85 },

  bubble: {
    position: "absolute",
    right: "100%",
    top: 4,
    marginRight: 8,
    backgroundColor: colors.card,
    borderRadius: 14,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    maxWidth: 120,
    shadowColor: "#19171A",
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  bubbleText: {
    fontFamily: fonts.serif,
    fontSize: 15,
    fontStyle: "italic",
    color: colors.accentInk,
  },
  bubbleTail: {
    position: "absolute",
    right: -5,
    top: 12,
    width: 10,
    height: 10,
    backgroundColor: colors.card,
    borderRightWidth: StyleSheet.hairlineWidth,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    transform: [{ rotate: "45deg" }],
  },

  face: {
    fontSize: 11,
    color: colors.ink3,
    marginTop: -2,
  },
  srOnly: {
    position: "absolute",
    width: 1,
    height: 1,
    opacity: 0,
  },
});
