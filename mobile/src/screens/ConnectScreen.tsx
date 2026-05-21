// Onboarding entry (PRD 9.1). One-sentence value prop, then Connect Gmail.
// Opens the backend-provided Google consent URL; the backend redirects back via
// the albert://auth deep link, handled in app/_layout.tsx.

import { useCallback, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import * as WebBrowser from "expo-web-browser";

import { api } from "@/api/client";
import { getToken } from "@/api/auth";
import { colors, spacing } from "@/theme/theme";

type Props = { onConnected: () => void };

export function ConnectScreen({ onConnected }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const connect = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const { authorization_url } = await api.startGoogleAuth();
      await WebBrowser.openAuthSessionAsync(authorization_url, "albert://auth");
      // The deep-link handler stores the token; re-check before advancing.
      if (await getToken()) onConnected();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start Google sign-in");
    } finally {
      setBusy(false);
    }
  }, [onConnected]);

  return (
    <View style={styles.screen}>
      <Text style={styles.title}>Albert</Text>
      <Text style={styles.tagline}>
        Connect Gmail and Calendar. I will find what matters, what you are forgetting, and what
        needs action.
      </Text>
      <Pressable style={styles.button} onPress={connect} disabled={busy}>
        <Text style={styles.buttonText}>{busy ? "Opening…" : "Connect Gmail"}</Text>
      </Pressable>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: spacing.xl,
    justifyContent: "center",
    gap: spacing.lg,
  },
  title: { color: colors.text, fontSize: 40, fontWeight: "800" },
  tagline: { color: colors.textMuted, fontSize: 16, lineHeight: 24 },
  button: { backgroundColor: colors.accent, borderRadius: 12, paddingVertical: spacing.md, alignItems: "center" },
  buttonText: { color: "#0E0F12", fontSize: 16, fontWeight: "700" },
  error: { color: "#E5484D", fontSize: 13 },
});
