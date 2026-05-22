// Placeholder for tabs whose screens land in later slices.

import { StyleSheet, Text, View } from "react-native";

import { Serif } from "@/components/ui";
import { colors, spacing } from "@/theme/theme";

export function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <View style={styles.screen}>
      <Serif size={26}>{title}</Serif>
      <Text style={styles.note}>{note}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.paper,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
    gap: spacing.sm,
  },
  note: {
    color: colors.ink3,
    fontSize: 14,
    lineHeight: 20,
    textAlign: "center",
  },
});
