// Onboarding entry (PRD 9.1). Editorial hero: 阿福 eyebrow, serif Albert wordmark,
// serif tagline, then Connect Gmail. Opens the backend-provided Google consent URL;
// the backend redirects back via the albert://auth deep link, handled in _layout.tsx.

import { useCallback, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import * as WebBrowser from "expo-web-browser";

import { api } from "@/api/client";
import { getToken, setToken } from "@/api/auth";
import {
  Btn,
  Eyebrow,
  Serif,
  inputPlaceholder,
  inputStyle,
} from "@/components/ui";
import { colors, fonts, radius, spacing } from "@/theme/theme";

type Props = { onConnected: () => void };

export function ConnectScreen({ onConnected }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [devEmail, setDevEmail] = useState("zeraikiadam@gmail.com");

  const connect = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const { authorization_url } = await api.startGoogleAuth();
      await WebBrowser.openAuthSessionAsync(authorization_url, "albert://auth");
      // The deep-link handler stores the token; re-check before advancing.
      if (await getToken()) onConnected();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not start Google sign-in",
      );
    } finally {
      setBusy(false);
    }
  }, [onConnected]);

  // Development only: skip the OAuth round-trip (which needs a LAN-reachable redirect
  // on a phone) by minting a session for an already-connected account.
  const devLogin = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const { access_token } = await api.devSession(devEmail.trim());
      await setToken(access_token);
      onConnected();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Dev login failed");
    } finally {
      setBusy(false);
    }
  }, [devEmail, onConnected]);

  return (
    <View style={styles.screen}>
      <Eyebrow>阿福 · Your chief of staff</Eyebrow>
      <Serif size={52} style={styles.title}>
        Albert
      </Serif>
      <Serif size={22} color={colors.ink2} style={styles.tagline}>
        Connect Gmail and Calendar. I'll find what matters, what you're
        forgetting, and what needs action.
      </Serif>

      <View style={styles.ctaWrap}>
        <Btn
          label={busy ? "Opening…" : "Connect Gmail"}
          kind="accent"
          onPress={connect}
          disabled={busy}
        />
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {__DEV__ ? (
        <View style={styles.devBox}>
          <Text style={styles.devLabel}>Dev login (skips OAuth)</Text>
          <TextInput
            style={[inputStyle, styles.devInput]}
            value={devEmail}
            onChangeText={setDevEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="email"
            placeholderTextColor={inputPlaceholder}
          />
          <Pressable
            style={styles.devButton}
            onPress={devLogin}
            disabled={busy}
          >
            <Text style={styles.devButtonText}>Dev sign in</Text>
          </Pressable>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.paper,
    padding: spacing.xl,
    justifyContent: "center",
  },
  title: { marginTop: spacing.sm },
  tagline: { marginTop: spacing.md, lineHeight: 29 },
  ctaWrap: { marginTop: spacing.xl, alignSelf: "flex-start" },
  error: { color: colors.warn, fontSize: 13, marginTop: spacing.sm },
  devBox: {
    marginTop: spacing.xl,
    padding: spacing.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.hair2,
    borderRadius: radius.sm,
    gap: spacing.sm,
  },
  devLabel: { fontFamily: fonts.mono, color: colors.ink3, fontSize: 12 },
  devInput: { borderRadius: radius.sm },
  devButton: {
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.accent,
    borderRadius: radius.pill,
    paddingVertical: spacing.sm,
    alignItems: "center",
  },
  devButtonText: { color: colors.accent, fontWeight: "600" },
});
