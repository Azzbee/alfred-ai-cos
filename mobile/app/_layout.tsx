// Root layout. Captures the albert://auth?token=... deep link from the OAuth
// callback and stores the session token before rendering the app.

import { useEffect } from "react";
import { Stack, useRouter } from "expo-router";
import * as Linking from "expo-linking";

import { setToken } from "@/api/auth";

export default function RootLayout() {
  const router = useRouter();

  useEffect(() => {
    const handle = async (url: string | null) => {
      if (!url) return;
      const parsed = Linking.parse(url);
      const token = parsed.queryParams?.token;
      if (parsed.path === "auth" && typeof token === "string") {
        await setToken(token);
        router.replace("/");
      }
    };

    void Linking.getInitialURL().then(handle);
    const sub = Linking.addEventListener("url", (e) => void handle(e.url));
    return () => sub.remove();
  }, [router]);

  return <Stack screenOptions={{ headerShown: false }} />;
}
