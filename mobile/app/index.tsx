// Entry route. Routes to connect (no session), onboarding (session but not yet
// calibrated), or the tabs (ready).

import { useEffect, useState } from "react";
import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";

import { useAuth } from "@/api/AuthContext";
import { api } from "@/api/client";
import { colors } from "@/theme/theme";

export default function Index() {
  const { authed } = useAuth();
  const [onboarded, setOnboarded] = useState<boolean | null>(null);

  useEffect(() => {
    if (authed) {
      api
        .getMe()
        .then((me) => setOnboarded(me.onboarded))
        .catch(() => setOnboarded(true)); // on error, do not trap the user in onboarding
    }
  }, [authed]);

  if (authed === false) return <Redirect href="/connect" />;

  if (authed === null || onboarded === null) {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: colors.paper,
          justifyContent: "center",
        }}
      >
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  return onboarded ? (
    <Redirect href="/(tabs)" />
  ) : (
    <Redirect href="/onboarding" />
  );
}
