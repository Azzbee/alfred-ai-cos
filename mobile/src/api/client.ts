// Thin typed fetch client for the Albert API. Reads the base URL from Expo config
// and attaches the session token from secure storage.

import Constants from "expo-constants";
import type {
  ActionProposal,
  AuthStartResponse,
  Briefing,
  CaptureResponse,
  Commitment,
  CommitmentStatus,
  Draft,
  DraftCreateRequest,
  MeetingPrep,
  SyncResponse,
  Task,
  TaskCreateRequest,
  TaskStatus,
  TodayDashboard,
  UpcomingMeeting,
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
};
