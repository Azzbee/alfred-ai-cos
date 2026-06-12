// Platform-aware secure-ish storage for session tokens and small app state.
//
// Native (iOS / Android / Expo Go): expo-secure-store → Keychain / Keystore.
// Web (expo start --web): SecureStore has no native module, so we fall back to
// localStorage. Web is dev-only; production builds target mobile.
//
// All auth + companion-meta persistence should go through this module so call
// sites never import expo-secure-store directly.

import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

/** True when the Keychain/Keystore-backed API is available (not web). */
function useSecureStore(): boolean {
  return Platform.OS === "ios" || Platform.OS === "android";
}

/** Read a string value, or null if missing. */
export async function readSecureItem(key: string): Promise<string | null> {
  if (useSecureStore()) {
    return SecureStore.getItemAsync(key);
  }
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(key);
}

/** Write a string value. */
export async function writeSecureItem(key: string, value: string): Promise<void> {
  if (useSecureStore()) {
    await SecureStore.setItemAsync(key, value);
    return;
  }
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(key, value);
  }
}

/** Remove a stored value. */
export async function deleteSecureItem(key: string): Promise<void> {
  if (useSecureStore()) {
    await SecureStore.deleteItemAsync(key);
    return;
  }
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(key);
  }
}
