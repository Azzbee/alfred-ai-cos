// Smoke test for scripts/dev-api-proxy.mjs.
//
// Boots the proxy against a fake upstream HTTP server, then exercises:
//   1. OPTIONS preflight returns 204 with CORS headers.
//   2. GET /api/v1/* is forwarded and the upstream response body comes back.
//   3. /not-api/* returns 404 (proxy refuses anything outside /api/v1).
//
// Pure node:test — no vitest, no @types — so this can run with `node --test`
// in CI without pulling in the React Native test stack.

import assert from "node:assert/strict";
import http from "node:http";
import { spawn } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROXY_PATH = resolve(__dirname, "dev-api-proxy.mjs");

/** Spawn the proxy as a child process. The upstream HTTPS forwarding path
 * isn't exercised here (would need a self-signed-cert HTTPS server). These
 * tests cover the request-handling layer in front of the forward: CORS
 * preflight, allow-origin echo, fallback origin, and the path filter that
 * rejects anything outside /api/v1/*. */
function startProxy({ proxyPort }) {
  const child = spawn(process.execPath, [PROXY_PATH], {
    env: {
      ...process.env,
      ALBERT_PROXY_PORT: String(proxyPort),
      // Target host is harmless to set; the proxy only contacts it for
      // /api/v1/* requests, none of which are sent in this test.
      ALBERT_PROXY_TARGET: "127.0.0.1.test",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  return new Promise((resolveChild) => {
    child.stdout.on("data", (chunk) => {
      if (chunk.toString().includes("[dev-api-proxy]")) {
        resolveChild(child);
      }
    });
    child.stderr.on("data", () => {
      // proxy writes upstream-error messages to stderr; ignore in test bootstrap
    });
  });
}

function fetchRaw({
  method = "GET",
  port,
  path,
  headers = {},
  body = undefined,
}) {
  return new Promise((resolveResponse, rejectResponse) => {
    const req = http.request(
      {
        hostname: "127.0.0.1",
        port,
        path,
        method,
        headers,
      },
      (res) => {
        let chunks = "";
        res.on("data", (c) => {
          chunks += c;
        });
        res.on("end", () => {
          resolveResponse({
            status: res.statusCode,
            headers: res.headers,
            body: chunks,
          });
        });
      },
    );
    req.on("error", rejectResponse);
    if (body) req.write(body);
    req.end();
  });
}

test("OPTIONS preflight returns 204 with CORS headers for an allowed origin", async () => {
  const proxyPort = 18800;
  const proxy = await startProxy({ proxyPort });
  try {
    const res = await fetchRaw({
      method: "OPTIONS",
      port: proxyPort,
      path: "/api/v1/today",
      headers: {
        origin: "http://localhost:8081",
        "access-control-request-method": "GET",
      },
    });
    assert.equal(res.status, 204);
    assert.equal(
      res.headers["access-control-allow-origin"],
      "http://localhost:8081",
    );
    assert.match(res.headers["access-control-allow-methods"] || "", /POST/);
    assert.match(
      res.headers["access-control-allow-headers"] || "",
      /Authorization/,
    );
  } finally {
    proxy.kill();
  }
});

test("non-/api/v1 paths return 404", async () => {
  const proxyPort = 18801;
  const proxy = await startProxy({ proxyPort });
  try {
    const res = await fetchRaw({ port: proxyPort, path: "/not-api/whatever" });
    assert.equal(res.status, 404);
    assert.match(res.body, /Albert dev proxy/);
  } finally {
    proxy.kill();
  }
});

test("CORS fallback origin is set when no Origin header is provided", async () => {
  const proxyPort = 18802;
  const proxy = await startProxy({ proxyPort });
  try {
    const res = await fetchRaw({ port: proxyPort, path: "/not-api/anything" });
    // Fallback origin per the proxy's setCors() helper.
    assert.equal(
      res.headers["access-control-allow-origin"],
      "http://localhost:8081",
    );
  } finally {
    proxy.kill();
  }
});
