// Push registration. Asks for permission, gets the Expo push token, and registers
// it with the backend. Safe to call repeatedly; the backend dedups on the token.

import { Platform } from "react-native";
import * as Notifications from "expo-notifications";

import { api } from "@/api/client";

export async function registerForPush(): Promise<boolean> {
  const settings = await Notifications.getPermissionsAsync();
  let status = settings.status;
  if (status !== "granted") {
    status = (await Notifications.requestPermissionsAsync()).status;
  }
  if (status !== "granted") return false;

  const token = (await Notifications.getExpoPushTokenAsync()).data;
  await api.registerDevice(token, Platform.OS);
  return true;
}
