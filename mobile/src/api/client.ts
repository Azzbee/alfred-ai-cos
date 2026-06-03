// Thin typed fetch client for the Albert API. Reads the base URL from Expo config
// and attaches the session token from secure storage.

import Constants from "expo-constants";
import { Platform } from "react-native";
import type {
  ActionProposal,
  AppNotification,
  AssistantAskResponse,
  AuthStartResponse,
  BookMessageResponse,
  Briefing,
  CaptureResponse,
  Commitment,
  CommitmentDraft,
  CommitmentStatus,
  Draft,
  DraftCreateRequest,
  InboxView,
  Me,
  MeetingPrep,
  OnboardingPrefs,
  SessionToken,
  SyncResponse,
  Task,
  TaskCreateRequest,
  TaskStatus,
  TodayDashboard,
  UpcomingMeeting,
  WaitingView,
} from "@albert/shared-types";

import { clearToken, getToken } from "./auth";

/**
 * API base URL resolution:
 *   • Native (Expo Go / device): production URL from app.json extra.apiBaseUrl
 *   • Web dev: localhost:8000 — requests go through scripts/dev-api-proxy.mjs
 *     which adds CORS headers and forwards to production (browser blocks direct
 *     cross-origin calls to albert.alfredassistants.com).
 *   • Fallback: localhost:8000 for local backend development.
 */
function resolveBaseUrl(): string {
  if (Platform.OS === "web" && __DEV__) {
    return "http://localhost:8000";
  }
  return (
    (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ??
    "http://localhost:8000"
  );
}

const BASE_URL = resolveBaseUrl();

// The device's IANA timezone (e.g. "Europe/Paris"), via Hermes' Intl. Falls back to
// UTC if unavailable. Sent with assistant requests so booked times match the user's clock.
function deviceTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

// The AuthContext registers a handler so a 401 (expired/invalid token, or a rotated
// server secret) drops the user back to Connect instead of looping on dead requests.
let onAuthExpired: (() => void) | null = null;
export function setOnAuthExpired(fn: (() => void) | null): void {
  onAuthExpired = fn;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      // Skip ngrok's free-tier interstitial so the app gets JSON, not the warning page.
      "ngrok-skip-browser-warning": "true",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    // A 401 while we hold a token means it's no longer valid — clear it and bounce to
    // Connect so the user (and friends) re-auth cleanly instead of looping on 401s.
    if (res.status === 401 && token) {
      await clearToken();
      onAuthExpired?.();
    }
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  // `redirect` is the app's own deep link to return to after Google sign-in
  // (Linking.createURL("auth")): albert://auth in a build, exp://…/--/auth in Expo Go.
  startGoogleAuth: (redirect: string) =>
    request<AuthStartResponse>(
      `/auth/google/start?redirect=${encodeURIComponent(redirect)}`,
    ),
  // Development only: mint a session for an already-connected account, bypassing the
  // mobile OAuth round-trip (which needs a LAN-reachable redirect URI). The backend
  // returns 404 outside ENVIRONMENT=development.
  devSession: (email: string) =>
    request<SessionToken>(
      `/auth/dev-session?email=${encodeURIComponent(email)}`,
      {
        method: "POST",
      },
    ),
  sync: () => request<SyncResponse>("/sync", { method: "POST" }),
  getToday: () => request<TodayDashboard>("/today"),
  getInbox: () => request<InboxView>("/messages"),
  // "Add to calendar" on a message — books it if it describes a timed event.
  bookFromMessage: (messageId: string, timezone: string) =>
    request<BookMessageResponse>(`/messages/${messageId}/book`, {
      method: "POST",
      body: JSON.stringify({ timezone }),
    }),
  // Ask Albert a free-text request ("book my calendar tomorrow 5-6pm"). Sends the
  // device timezone so "5pm" resolves to the user's wall clock, not the server default.
  ask: (text: string) =>
    request<AssistantAskResponse>("/assistant/ask", {
      method: "POST",
      body: JSON.stringify({ text, timezone: deviceTimezone() }),
    }),
  listCommitments: () => request<Commitment[]>("/commitments"),
  updateCommitmentStatus: (id: string, status: CommitmentStatus) =>
    request<Commitment>(`/commitments/${id}/status?status=${status}`, {
      method: "POST",
    }),
  // Draft a reply for a Today priority ("Act"). Returns real recipient/subject/body/
  // evidence generated from the commitment, not a stored Gmail draft.
  draftForCommitment: (id: string, tone = "concise") =>
    request<CommitmentDraft>(`/commitments/${id}/draft`, {
      method: "POST",
      body: JSON.stringify({ tone }),
    }),
  createDraft: (body: DraftCreateRequest) =>
    request<Draft>("/drafts", { method: "POST", body: JSON.stringify(body) }),
  proposeDraftToGmail: (draftId: string) =>
    request<ActionProposal>(`/actions/propose-draft-to-gmail/${draftId}`, {
      method: "POST",
    }),
  // Propose SENDING a stored draft (level 3, gmail.send). Pair with approveAction.
  proposeSendDraft: (draftId: string) =>
    request<ActionProposal>(`/actions/propose-send-draft/${draftId}`, {
      method: "POST",
    }),
  approveAction: (actionId: string, confirm = false) =>
    request<ActionProposal>(`/actions/${actionId}/approve?confirm=${confirm}`, {
      method: "POST",
    }),
  rejectAction: (actionId: string) =>
    request<ActionProposal>(`/actions/${actionId}/reject`, { method: "POST" }),
  listPendingActions: () => request<ActionProposal[]>("/actions/pending"),
  listUpcomingMeetings: () => request<UpcomingMeeting[]>("/meetings/upcoming"),
  getMeetingPrep: (eventId: string) =>
    request<MeetingPrep>(`/meetings/${eventId}/prep`),
  generateBriefing: () =>
    request<Briefing>("/briefings/generate", { method: "POST" }),
  getTodayBriefing: () => request<Briefing>("/briefings/today"),
  briefingFeedback: (id: string, useful: boolean) =>
    request<Briefing>(`/briefings/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ useful }),
    }),
  createTask: (body: TaskCreateRequest) =>
    request<Task>("/tasks", { method: "POST", body: JSON.stringify(body) }),
  listTasks: () => request<Task[]>("/tasks"),
  updateTaskStatus: (id: string, status: TaskStatus) =>
    request<Task>(`/tasks/${id}/status?status=${status}`, { method: "POST" }),
  captureText: (text: string) =>
    request<CaptureResponse>("/capture", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  captureVoice: async (uri: string): Promise<CaptureResponse> => {
    const token = await getToken();
    const form = new FormData();
    // React Native FormData accepts a { uri, name, type } file object.
    form.append("audio", {
      uri,
      name: "note.m4a",
      type: "audio/m4a",
    } as unknown as Blob);
    const res = await fetch(`${BASE_URL}/api/v1/capture/voice`, {
      method: "POST",
      headers: {
        "ngrok-skip-browser-warning": "true",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: form,
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return (await res.json()) as CaptureResponse;
  },
  getWaiting: () => request<WaitingView>("/waiting"),
  getMe: () => request<Me>("/me"),
  submitOnboarding: (prefs: OnboardingPrefs) =>
    request<Me>("/onboarding", { method: "POST", body: JSON.stringify(prefs) }),
  registerDevice: (push_token: string, platform?: string) =>
    request<void>("/devices", {
      method: "POST",
      body: JSON.stringify({ push_token, platform }),
    }),
  listNotifications: () => request<AppNotification[]>("/notifications"),
  notificationFeedback: (id: string, useful: boolean) =>
    request<AppNotification>(`/notifications/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ useful }),
    }),
  setQuietHours: (quiet_hours: string) =>
    request<void>("/notifications/prefs", {
      method: "POST",
      body: JSON.stringify({ quiet_hours }),
    }),
  disconnectAccount: (provider: string) =>
    request<void>(`/connected-accounts/${provider}`, { method: "DELETE" }),
  deleteAccount: () => request<void>("/me", { method: "DELETE" }),
};
