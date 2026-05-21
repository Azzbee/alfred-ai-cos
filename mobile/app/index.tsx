// Entry route. Shows the Connect screen until a session token exists, then Today.

import { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";

import { getToken } from "@/api/auth";
import { ConnectScreen } from "@/screens/ConnectScreen";
import { TodayScreen } from "@/screens/TodayScreen";
import { colors } from "@/theme/theme";

export default function Index() {
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    void getToken().then((t) => setAuthed(Boolean(t)));
  }, []);

  if (authed === null) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg, justifyContent: "center" }}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  return authed ? <TodayScreen /> : <ConnectScreen onConnected={() => setAuthed(true)} />;
}
