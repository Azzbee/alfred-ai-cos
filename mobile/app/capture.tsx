// Full-screen capture route, presented over the tabs (the prototype's center "+").
// Closes back to Today; CaptureScreen reloads the dashboard on confirm.

import { useRouter } from "expo-router";

import { CaptureScreen } from "@/screens/CaptureScreen";

export default function Capture() {
  const router = useRouter();
  return <CaptureScreen onClose={() => router.back()} />;
}
