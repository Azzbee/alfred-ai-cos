// Onboarding calibration (PRD 9.1). Three questions, then writes to preferences.
// Editorial theme: serif header, mono prompts, accent-tinted selected chips.

import { useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import type { OnboardingPrefs } from "@albert/shared-types";

import { api } from "@/api/client";
import {
  Btn,
  ScreenHeader,
  inputPlaceholder,
  inputStyle,
} from "@/components/ui";
import { colors, fonts, radius, spacing } from "@/theme/theme";

type Question = {
  key: keyof OnboardingPrefs;
  prompt: string;
  options: { value: string; label: string }[];
};

const QUESTIONS: Question[] = [
  {
    key: "focus",
    prompt: "What do you mainly want help with?",
    options: [
      { value: "work", label: "Work" },
      { value: "school", label: "School" },
      { value: "personal", label: "Personal admin" },
      { value: "founder", label: "Founder / startup" },
      { value: "all", label: "All of the above" },
    ],
  },
  {
    key: "optimize_for",
    prompt: "What should Albert optimize for?",
    options: [
      { value: "deadlines", label: "Never miss deadlines" },
      { value: "priorities", label: "Clear daily priorities" },
      { value: "follow_ups", label: "Better follow-ups" },
      { value: "meetings", label: "Meeting preparation" },
      { value: "inbox", label: "Inbox control" },
    ],
  },
  {
    key: "proactiveness",
    prompt: "How proactive should Albert be?",
    options: [
      { value: "quiet", label: "Quiet" },
      { value: "balanced", label: "Balanced" },
      { value: "very_proactive", label: "Very proactive" },
    ],
  },
];

export function OnboardingScreen({ onDone }: { onDone: () => void }) {
  const [prefs, setPrefs] = useState<OnboardingPrefs>({});
  const [saving, setSaving] = useState(false);

  const allAnswered =
    Boolean(prefs.name?.trim()) && QUESTIONS.every((q) => prefs[q.key]);

  const submit = async () => {
    setSaving(true);
    try {
      await api.submitOnboarding(prefs);
      onDone();
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <ScreenHeader
        eyebrow="Welcome"
        title="Set up Albert"
        subtitle="A few quick questions so Albert knows what matters to you."
      />

      <View style={styles.block}>
        <Text style={styles.prompt}>What should Albert call you?</Text>
        <TextInput
          style={inputStyle}
          placeholder="Your name (used to sign drafts)"
          placeholderTextColor={inputPlaceholder}
          value={prefs.name ?? ""}
          onChangeText={(t) => setPrefs((p) => ({ ...p, name: t }))}
          autoCapitalize="words"
        />
      </View>

      {QUESTIONS.map((q) => (
        <View key={q.key} style={styles.block}>
          <Text style={styles.prompt}>{q.prompt}</Text>
          <View style={styles.options}>
            {q.options.map((o) => {
              const selected = prefs[q.key] === o.value;
              return (
                <Pressable
                  key={o.value}
                  style={[styles.option, selected && styles.optionSelected]}
                  onPress={() => setPrefs((p) => ({ ...p, [q.key]: o.value }))}
                >
                  <Text
                    style={[
                      styles.optionText,
                      selected && styles.optionTextSelected,
                    ]}
                  >
                    {o.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ))}

      <View style={styles.ctaWrap}>
        <Btn
          label={saving ? "Saving…" : "Start using Albert"}
          kind="accent"
          onPress={() => void submit()}
          disabled={!allAnswered || saving}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.paper },
  content: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
    gap: spacing.lg,
  },
  block: { gap: spacing.sm },
  prompt: {
    fontFamily: fonts.mono,
    fontSize: 12,
    letterSpacing: 0.6,
    textTransform: "uppercase",
    color: colors.ink3,
  },
  options: { gap: spacing.sm },
  option: {
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    borderRadius: radius.sm,
    padding: spacing.md,
  },
  optionSelected: {
    borderColor: colors.accent,
    backgroundColor: colors.accentSoft,
  },
  optionText: { color: colors.ink, fontSize: 15 },
  optionTextSelected: { color: colors.accentInk, fontWeight: "600" },
  ctaWrap: { marginTop: spacing.sm },
});
