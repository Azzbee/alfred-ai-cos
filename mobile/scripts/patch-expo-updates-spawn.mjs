#!/usr/bin/env node
/**
 * Node 24 + cross-spawn hangs when executing expo-updates/bin/cli.js via shebang.
 * That blocks Expo Go manifest responses (Metro /status works, / manifest hangs).
 *
 * Patch @expo/cli to spawn: node expo-updates/bin/cli.js …
 * Idempotent — safe to run on every start:phone / postinstall.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const mobileDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(mobileDir, "..");
const target = path.join(
  repoRoot,
  "node_modules/@expo/cli/build/src/utils/expoUpdatesCli.js",
);

const ORIGINAL =
  "return (await (0, _spawnasync().default)(expoUpdatesCli, args, {";
const PATCHED =
  "return (await (0, _spawnasync().default)(process.execPath, [expoUpdatesCli, ...args], {";

if (!fs.existsSync(target)) {
  console.warn("[patch-expo-updates-spawn] @expo/cli not installed — skipping");
  process.exit(0);
}

const text = fs.readFileSync(target, "utf8");
if (text.includes(PATCHED)) {
  process.exit(0);
}

if (!text.includes(ORIGINAL)) {
  console.error(
    "[patch-expo-updates-spawn] Unexpected @expo/cli source — manual check needed:",
    target,
  );
  process.exit(1);
}

fs.writeFileSync(target, text.replace(ORIGINAL, PATCHED, 1));
console.log("[patch-expo-updates-spawn] Patched expo-updates spawn for Node 24 ✓");
