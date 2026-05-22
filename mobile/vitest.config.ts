// Vitest config for the mobile app's pure-logic unit tests. These tests cover the
// UI-free modules (src/lib, the deterministic helpers in ui/data) without a React
// Native runtime, so no native-module mocks are needed. Screen render tests would
// require jest-expo; this config deliberately stays light.

import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
      "@albert/shared-types": resolve(
        __dirname,
        "../packages/shared-types/src/index.ts",
      ),
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
