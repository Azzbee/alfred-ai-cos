// secureStorage.ts wraps expo-secure-store on native and localStorage on web.
// Both backends are mocked so the contract — "the right backend is selected by
// Platform.OS, and the calls round-trip" — is exercised in isolation.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// react-native + expo-secure-store don't load under a Node test runner. Mock
// both before importing the SUT so the import doesn't blow up.
const secureStoreMock = {
  getItemAsync: vi.fn<(k: string) => Promise<string | null>>(),
  setItemAsync: vi.fn<(k: string, v: string) => Promise<void>>(),
  deleteItemAsync: vi.fn<(k: string) => Promise<void>>(),
};
vi.mock("expo-secure-store", () => secureStoreMock);

const platformMock = { OS: "ios" as "ios" | "android" | "web" };
vi.mock("react-native", () => ({ Platform: platformMock }));

// Local in-memory localStorage shim for the web path.
class FakeLocalStorage {
  private store = new Map<string, string>();
  getItem(k: string): string | null {
    return this.store.has(k) ? this.store.get(k)! : null;
  }
  setItem(k: string, v: string): void {
    this.store.set(k, v);
  }
  removeItem(k: string): void {
    this.store.delete(k);
  }
}

beforeEach(() => {
  vi.resetModules();
  secureStoreMock.getItemAsync.mockReset();
  secureStoreMock.setItemAsync.mockReset();
  secureStoreMock.deleteItemAsync.mockReset();
  platformMock.OS = "ios";
  // Mocked-out global to mirror the browser API the SUT falls back to on web.
  (globalThis as unknown as { localStorage?: FakeLocalStorage }).localStorage =
    new FakeLocalStorage();
});

afterEach(() => {
  delete (globalThis as unknown as { localStorage?: FakeLocalStorage })
    .localStorage;
});

async function importSut(): Promise<typeof import("./secureStorage")> {
  return import("./secureStorage");
}

describe("native path (Platform.OS === ios)", () => {
  it("reads through SecureStore.getItemAsync", async () => {
    secureStoreMock.getItemAsync.mockResolvedValueOnce("native-value");
    const { readSecureItem } = await importSut();
    await expect(readSecureItem("jwt")).resolves.toBe("native-value");
    expect(secureStoreMock.getItemAsync).toHaveBeenCalledWith("jwt");
  });

  it("writes through SecureStore.setItemAsync", async () => {
    secureStoreMock.setItemAsync.mockResolvedValueOnce(undefined);
    const { writeSecureItem } = await importSut();
    await writeSecureItem("jwt", "abc.def");
    expect(secureStoreMock.setItemAsync).toHaveBeenCalledWith("jwt", "abc.def");
  });

  it("deletes through SecureStore.deleteItemAsync", async () => {
    secureStoreMock.deleteItemAsync.mockResolvedValueOnce(undefined);
    const { deleteSecureItem } = await importSut();
    await deleteSecureItem("jwt");
    expect(secureStoreMock.deleteItemAsync).toHaveBeenCalledWith("jwt");
  });

  it("never falls back to localStorage on native", async () => {
    secureStoreMock.getItemAsync.mockResolvedValueOnce("from-native");
    const { readSecureItem } = await importSut();
    await readSecureItem("k");
    // We didn't read from localStorage even though it exists in the test env.
    expect(
      (
        globalThis as unknown as { localStorage: FakeLocalStorage }
      ).localStorage.getItem("k"),
    ).toBeNull();
  });
});

describe("android path (Platform.OS === android)", () => {
  it("uses SecureStore the same way as ios", async () => {
    platformMock.OS = "android";
    secureStoreMock.getItemAsync.mockResolvedValueOnce("droid");
    const { readSecureItem } = await importSut();
    await expect(readSecureItem("jwt")).resolves.toBe("droid");
    expect(secureStoreMock.getItemAsync).toHaveBeenCalledWith("jwt");
  });
});

describe("web fallback (Platform.OS === web)", () => {
  it("reads from localStorage", async () => {
    platformMock.OS = "web";
    (
      globalThis as unknown as { localStorage: FakeLocalStorage }
    ).localStorage.setItem("jwt", "from-web");
    const { readSecureItem } = await importSut();
    await expect(readSecureItem("jwt")).resolves.toBe("from-web");
    expect(secureStoreMock.getItemAsync).not.toHaveBeenCalled();
  });

  it("writes to localStorage", async () => {
    platformMock.OS = "web";
    const { writeSecureItem } = await importSut();
    await writeSecureItem("jwt", "v1");
    expect(
      (
        globalThis as unknown as { localStorage: FakeLocalStorage }
      ).localStorage.getItem("jwt"),
    ).toBe("v1");
    expect(secureStoreMock.setItemAsync).not.toHaveBeenCalled();
  });

  it("delete is idempotent on a missing key", async () => {
    platformMock.OS = "web";
    const { deleteSecureItem } = await importSut();
    await expect(deleteSecureItem("missing")).resolves.toBeUndefined();
  });

  it("read returns null when there's no value", async () => {
    platformMock.OS = "web";
    const { readSecureItem } = await importSut();
    await expect(readSecureItem("never-set")).resolves.toBeNull();
  });

  it("returns null when localStorage is unavailable", async () => {
    platformMock.OS = "web";
    delete (globalThis as unknown as { localStorage?: FakeLocalStorage })
      .localStorage;
    const { readSecureItem } = await importSut();
    await expect(readSecureItem("anything")).resolves.toBeNull();
  });
});
