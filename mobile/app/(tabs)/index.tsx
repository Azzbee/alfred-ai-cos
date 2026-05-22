// The tab container, built from plain primitives. No native navigator.
//
// Expo Go SDK 54 forces the New Architecture, under which expo-router's <Tabs> bar
// (react-native-screens) throws on render. So we render the active screen via local
// state and draw the prototype's custom bottom bar: Today · Inbox · (center Capture +)
// · Ask · You. Capture pushes the full-screen /capture route over the tabs.

import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { Ic } from "@/components/icons";
import { ShellProvider } from "@/components/Shell";
import { AskScreen } from "@/screens/AskScreen";
import { InboxScreen } from "@/screens/InboxScreen";
import { SettingsScreen } from "@/screens/SettingsScreen";
import { TodayScreen } from "@/screens/TodayScreen";
import { colors, fonts, layout } from "@/theme/theme";

type TabKey = "today" | "inbox" | "ask" | "settings";

export default function TabsHome() {
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("today");

  return (
    <ShellProvider>
      <View style={styles.root}>
        <View style={styles.content}>
          {tab === "today" ? <TodayScreen /> : null}
          {tab === "inbox" ? <InboxScreen /> : null}
          {tab === "ask" ? <AskScreen /> : null}
          {tab === "settings" ? <SettingsScreen /> : null}
        </View>

        <View style={styles.bar}>
          <Tab
            label="Today"
            active={tab === "today"}
            onPress={() => setTab("today")}
            icon={(c) => <Ic.Today size={22} color={c} stroke={1.5} />}
          />
          <Tab
            label="Inbox"
            active={tab === "inbox"}
            onPress={() => setTab("inbox")}
            icon={(c) => <Ic.Inbox size={22} color={c} stroke={1.5} />}
          />
          <Pressable
            style={styles.capture}
            onPress={() => router.push("/capture")}
            accessibilityLabel="Capture"
          >
            <Ic.Plus size={22} color={colors.paper} stroke={2} />
          </Pressable>
          <Tab
            label="Ask"
            active={tab === "ask"}
            onPress={() => setTab("ask")}
            icon={(c) => <Ic.Stack size={22} color={c} stroke={1.5} />}
          />
          <Tab
            label="You"
            active={tab === "settings"}
            onPress={() => setTab("settings")}
            icon={(c) => <Ic.User size={22} color={c} stroke={1.5} />}
          />
        </View>
      </View>
    </ShellProvider>
  );
}

function Tab({
  label,
  active,
  onPress,
  icon,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  icon: (color: string) => React.ReactNode;
}) {
  const color = active ? colors.accent : colors.ink4;
  return (
    <Pressable style={styles.tab} onPress={onPress}>
      {icon(color)}
      <Text style={[styles.label, { color }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
  content: { flex: 1 },
  bar: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hair,
    backgroundColor: colors.paper,
    paddingBottom: layout.padX + 4,
    paddingTop: 8,
    paddingHorizontal: 14,
  },
  tab: {
    alignItems: "center",
    gap: 3,
    paddingVertical: 8,
    paddingHorizontal: 10,
  },
  label: {
    fontFamily: fonts.mono,
    fontSize: 9,
    letterSpacing: 0.9,
    textTransform: "uppercase",
  },
  // Center capture: lifted ink circle with a paper ring + shadow.
  capture: {
    width: 52,
    height: 52,
    borderRadius: 26,
    marginTop: -18,
    backgroundColor: colors.ink,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 4,
    borderColor: colors.paper,
    shadowColor: "#19171A",
    shadowOpacity: 0.18,
    shadowRadius: 22,
    shadowOffset: { width: 0, height: 8 },
  },
});
