// App shell: the sheet host + toast, exposed through a context so any screen can
// open a bottom sheet (meeting prep, approval) or fire a toast — the prototype's
// setSheet / showToast. The tab bar lives in app/(tabs)/index.tsx and renders the
// active screen; this provider wraps it and draws the overlays on top.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Animated,
  Easing,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Ic } from "@/components/icons";
import { colors, layout, radius } from "@/theme/theme";

type SheetContent = ReactNode | null;

// An optional tappable action on a toast (e.g. "Undo"). Tapping fires `onPress` and
// dismisses the toast.
type ToastAction = { label: string; onPress: () => void };

type ToastState = { message: string; action?: ToastAction } | null;

type ShellApi = {
  openSheet: (content: ReactNode) => void;
  closeSheet: () => void;
  // `action` adds a tappable affordance; `duration` overrides the default 2.2s
  // (use a longer window when there's an Undo to catch).
  showToast: (
    message: string,
    opts?: { action?: ToastAction; duration?: number },
  ) => void;
};

const ShellContext = createContext<ShellApi | null>(null);

export function useShell(): ShellApi {
  const ctx = useContext(ShellContext);
  if (!ctx) throw new Error("useShell must be used within <ShellProvider>");
  return ctx;
}

export function ShellProvider({ children }: { children: ReactNode }) {
  const [sheet, setSheet] = useState<SheetContent>(null);
  const [toast, setToast] = useState<ToastState>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const openSheet = useCallback((content: ReactNode) => setSheet(content), []);
  const closeSheet = useCallback(() => setSheet(null), []);

  const dismissToast = useCallback(() => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(null);
  }, []);

  const showToast = useCallback<ShellApi["showToast"]>((message, opts) => {
    setToast({ message, action: opts?.action });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(
      () => setToast(null),
      opts?.duration ?? 2200,
    );
  }, []);

  const api = useMemo<ShellApi>(
    () => ({ openSheet, closeSheet, showToast }),
    [openSheet, closeSheet, showToast],
  );

  return (
    <ShellContext.Provider value={api}>
      {children}
      <Sheet content={sheet} onClose={closeSheet} />
      <Toast
        toast={toast}
        onAction={() => {
          toast?.action?.onPress();
          dismissToast();
        }}
      />
    </ShellContext.Provider>
  );
}

// ── Bottom sheet ────────────────────────────────────────────────────────────
// Backdrop (ink @ 34%) + paper panel, top corners 26, grab handle, slide-up.

function Sheet({
  content,
  onClose,
}: {
  content: SheetContent;
  onClose: () => void;
}) {
  const slide = useRef(new Animated.Value(0)).current;
  const visible = content != null;

  // Drive slide-up when the sheet becomes visible; reset when it closes.
  useEffect(() => {
    if (visible) {
      Animated.timing(slide, {
        toValue: 1,
        duration: 280,
        easing: Easing.bezier(0.2, 0.7, 0.2, 1),
        useNativeDriver: true,
      }).start();
    } else {
      slide.setValue(0);
    }
  }, [visible, slide]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <Pressable style={styles.backdrop} onPress={onClose} />
      <Animated.View
        style={[
          styles.sheet,
          {
            transform: [
              {
                translateY: slide.interpolate({
                  inputRange: [0, 1],
                  outputRange: [600, 0],
                }),
              },
            ],
          },
        ]}
      >
        <View style={styles.grab} />
        <View style={styles.sheetBody}>{content}</View>
      </Animated.View>
    </Modal>
  );
}

// ── Toast ────────────────────────────────────────────────────────────────────

function Toast({
  toast,
  onAction,
}: {
  toast: ToastState;
  onAction: () => void;
}) {
  if (!toast) return null;
  const hasAction = toast.action != null;
  return (
    // Let touches through except on the toast itself, so the Undo is tappable but the
    // toast never blocks the screen behind it.
    <View pointerEvents="box-none" style={styles.toastWrap}>
      <View style={styles.toast}>
        <Ic.Check size={14} color="#fff" stroke={2.4} />
        <Text style={styles.toastText}>{toast.message}</Text>
        {hasAction ? (
          <Pressable
            hitSlop={8}
            onPress={onAction}
            style={({ pressed }) => [
              styles.toastAction,
              pressed && { opacity: 0.6 },
            ]}
          >
            <Text style={styles.toastActionText}>{toast.action?.label}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(25,23,26,0.34)",
  },
  sheet: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    maxHeight: "86%",
    backgroundColor: colors.paper,
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    paddingHorizontal: layout.padX,
    paddingTop: 8,
    paddingBottom: 18,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 30,
    shadowOffset: { width: 0, height: -20 },
  },
  grab: {
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.ink4,
    opacity: 0.4,
    alignSelf: "center",
    marginTop: 8,
    marginBottom: 14,
  },
  // flexShrink + minHeight:0 lets a tall sheet body shrink to the capped sheet height
  // so the inner ScrollView gets a bounded, scrollable area (instead of overflowing
  // and clipping the bottom).
  sheetBody: { flexShrink: 1, minHeight: 0 },
  toastWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 100,
    alignItems: "center",
  },
  toast: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.ink,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: radius.pill,
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 30,
    shadowOffset: { width: 0, height: 10 },
  },
  toastText: { color: colors.paper, fontSize: 13 },
  toastAction: {
    marginLeft: 4,
    paddingLeft: 12,
    borderLeftWidth: StyleSheet.hairlineWidth,
    borderLeftColor: "rgba(255,255,255,0.25)",
  },
  toastActionText: {
    color: colors.paper,
    fontSize: 13,
    fontWeight: "700",
  },
});
