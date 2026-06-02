// Root layout. Loads the brand fonts (Instrument Serif + Geist Mono, the heart of the
// editorial design), provides auth state, and captures the albert://auth?token=... deep
// link from the OAuth callback. Holds the splash until fonts are ready so there's no
// flash of system type.

import { useEffect } from "react";
import { Slot, router } from "expo-router";
import * as Linking from "expo-linking";
import * as Notifications from "expo-notifications";
import * as SplashScreen from "expo-splash-screen";
import {
  useFonts,
  InstrumentSerif_400Regular,
} from "@expo-google-fonts/instrument-serif";
import {
  GeistMono_400Regular,
  GeistMono_500Medium,
} from "@expo-google-fonts/geist-mono";
import {
  Geist_400Regular,
  Geist_500Medium,
  Geist_600SemiBold,
} from "@expo-google-fonts/geist";

import { setToken } from "@/api/auth";
import { AuthProvider, useAuth } from "@/api/AuthContext";
import { colors } from "@/theme/theme";
import { View } from "react-native";

void SplashScreen.preventAutoHideAsync();

function DeepLinkHandler() {
  const { refresh } = useAuth();

  useEffect(() => {
    const handle = async (url: string | null) => {
      if (!url) return;
      const parsed = Linking.parse(url);
      const token = parsed.queryParams?.token;
      if (parsed.path === "auth" && typeof token === "string") {
        await setToken(token);
        await refresh();
      }
    };

    void Linking.getInitialURL().then(handle);
    const sub = Linking.addEventListener("url", (e) => void handle(e.url));
    return () => sub.remove();
  }, [refresh]);

  // Route push taps to the embedded deep_link (e.g. "/approvals"). Set on both the
  // foreground/background tap stream and the cold-start response.
  useEffect(() => {
    const go = (data: unknown) => {
      const link = (data as { deep_link?: unknown })?.deep_link;
      if (typeof link === "string" && link.startsWith("/")) {
        router.push(link as never);
      }
    };
    void Notifications.getLastNotificationResponseAsync().then((r) => {
      if (r) go(r.notification.request.content.data);
    });
    const sub = Notifications.addNotificationResponseReceivedListener((r) =>
      go(r.notification.request.content.data),
    );
    return () => sub.remove();
  }, []);

  return <Slot />;
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    InstrumentSerif_400Regular,
    GeistMono_400Regular,
    GeistMono_500Medium,
  });

  useEffect(() => {
    if (fontsLoaded) void SplashScreen.hideAsync();
  }, [fontsLoaded]);

  if (!fontsLoaded) {
    return <View style={{ flex: 1, backgroundColor: colors.paper }} />;
  }

  return (
    <AuthProvider>
      <DeepLinkHandler />
    </AuthProvider>
  );
}
