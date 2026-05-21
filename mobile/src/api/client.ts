// Thin typed fetch client for the Albert API. Reads the base URL from Expo config
// and attaches the session token from secure storage.

import Constants from "expo-constants";
import type {
  ActionProposal,
  AppNotification,
  AuthStartResponse,
  Briefing,
  CaptureResponse,
  Commitment,
  CommitmentStatus,
  Draft,
  DraftCreateRequest,
  Me,
  MeetingPrep,
  OnboardingPrefs,
  SyncResponse,
  Task,
  TaskCreateRequest,
  TaskStatus,
  TodayDashboard,
  UpcomingMeeting,
  WaitingView,
} from "@albert/shared-types";

import { getToken } from "./auth";

const BASE_URL: string =
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ??
  "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  startGoogleAuth: () => request<AuthStartResponse>("/auth/google/start"),
  sync: () => request<SyncResponse>("/sync", { method: "POST" }),
  getToday: () => request<TodayDashboard>("/today"),
  listCommitments: () => request<Commitment[]>("/commitments"),
  updateCommitmentStatus: (id: string, status: CommitmentStatus) =>
    request<Commitment>(`/commitments/${id}/status?status=${status}`, {
      method: "POST",
    }),
  createDraft: (body: DraftCreateRequest) =>
    request<Draft>("/drafts", { method: "POST", body: JSON.stringify(body) }),
  proposeDraftToGmail: (draftId: string) =>
    request<ActionProposal>(`/actions/propose-draft-to-gmail/${draftId}`, {
      method: "POST",
    }),
  approveAction: (actionId: string) =>
    request<ActionProposal>(`/actions/${actionId}/approve`, { method: "POST" }),
  rejectAction: (actionId: string) =>
    request<ActionProposal>(`/actions/${actionId}/reject`, { method: "POST" }),
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
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
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
};
