// Onboarding calibration (PRD 9.1). Three questions, then writes to preferences.

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
import { colors, spacing } from "@/theme/theme";

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
      <Text style={styles.title}>Set up Albert</Text>
      <Text style={styles.sub}>
        A few quick questions so Albert knows what matters to you.
      </Text>

      <View style={styles.block}>
        <Text style={styles.prompt}>What should Albert call you?</Text>
        <TextInput
          style={styles.nameInput}
          placeholder="Your name (used to sign drafts)"
          placeholderTextColor={colors.textMuted}
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

      <Pressable
        style={[styles.cta, !allAnswered && styles.ctaDisabled]}
        onPress={() => void submit()}
        disabled={!allAnswered || saving}
      >
        <Text style={styles.ctaText}>
          {saving ? "Saving…" : "Start using Albert"}
        </Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.lg },
  title: { color: colors.text, fontSize: 28, fontWeight: "800" },
  sub: { color: colors.textMuted, fontSize: 14 },
  block: { gap: spacing.sm },
  prompt: { color: colors.text, fontSize: 16, fontWeight: "600" },
  nameInput: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    color: colors.text,
  },
  options: { gap: spacing.sm },
  option: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: spacing.md,
  },
  optionSelected: { borderColor: colors.accent, backgroundColor: "#1B2433" },
  optionText: { color: colors.text, fontSize: 15 },
  optionTextSelected: { color: colors.accent, fontWeight: "600" },
  cta: {
    backgroundColor: colors.accent,
    borderRadius: 12,
    paddingVertical: spacing.md,
    alignItems: "center",
  },
  ctaDisabled: { opacity: 0.4 },
  ctaText: { color: "#0E0F12", fontSize: 16, fontWeight: "700" },
});
