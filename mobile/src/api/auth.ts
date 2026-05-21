// Session token storage. The Albert session JWT lives in the device secure store,
// never in plain AsyncStorage. The token arrives via the albert://auth?token=...
// deep link after Google OAuth completes on the backend.

import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "albert.session_token";

export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function setToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}
