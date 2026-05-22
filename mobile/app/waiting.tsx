// Waiting tracker route, reached from Today's "Waiting on you" section. The full
// two-way view (people waiting on you / you waiting on them) wired to getWaiting().
// Wrapped in its own ShellProvider so the follow-up Approval sheet + toast work here.

import { ShellProvider } from "@/components/Shell";
import { WaitingScreen } from "@/screens/WaitingScreen";

export default function Waiting() {
  return (
    <ShellProvider>
      <WaitingScreen />
    </ShellProvider>
  );
}
