#!/usr/bin/env node
/**
 * Dev-only API proxy for Expo web preview.
 *
 * Browser CORS blocks http://localhost:8081 → https://albert.alfredassistants.com.
 * This tiny server listens on :8000, adds CORS headers, and forwards /api/v1/*
 * to the production backend so web dev login + API calls work without a full
 * local Postgres/Redis stack.
 *
 * Usage (separate terminal):  node scripts/dev-api-proxy.mjs
 * Or use:                     bun run start:web  (starts proxy + Expo together)
 */

import http from "node:http";
import https from "node:https";

const PROXY_PORT = Number(process.env.ALBERT_PROXY_PORT ?? 8000);
const TARGET_HOST =
  process.env.ALBERT_PROXY_TARGET ?? "albert.alfredassistants.com";

/** Origins allowed during local web dev (Expo web + alternate ports). */
const ALLOWED_ORIGINS = new Set([
  "http://localhost:8081",
  "http://127.0.0.1:8081",
  "http://localhost:8082",
  "http://127.0.0.1:8082",
  "http://localhost:19006",
  "http://127.0.0.1:19006",
]);

function setCors(req, res) {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
  } else {
    // Fallback for tools without Origin header.
    res.setHeader("Access-Control-Allow-Origin", "http://localhost:8081");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization, ngrok-skip-browser-warning",
  );
  res.setHeader("Access-Control-Max-Age", "86400");
}

const server = http.createServer((req, res) => {
  setCors(req, res);

  // Preflight — browser sends OPTIONS before POST / dev-session.
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (!req.url?.startsWith("/api/v1")) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Albert dev proxy — only /api/v1/* is forwarded.");
    return;
  }

  const forwardHeaders = { ...req.headers, host: TARGET_HOST };
  delete forwardHeaders.host;
  forwardHeaders.host = TARGET_HOST;

  const upstream = https.request(
    {
      hostname: TARGET_HOST,
      port: 443,
      path: req.url,
      method: req.method,
      headers: forwardHeaders,
    },
    (upstreamRes) => {
      setCors(req, res);
      res.writeHead(upstreamRes.statusCode ?? 502, upstreamRes.headers);
      upstreamRes.pipe(res);
    },
  );

  upstream.on("error", (err) => {
    console.error("[dev-api-proxy] upstream error:", err.message);
    res.writeHead(502, { "Content-Type": "text/plain" });
    res.end(`Proxy error: ${err.message}`);
  });

  req.pipe(upstream);
});

server.listen(PROXY_PORT, "127.0.0.1", () => {
  console.log(
    `[dev-api-proxy] http://127.0.0.1:${PROXY_PORT}/api/v1/* → https://${TARGET_HOST}/api/v1/*`,
  );
});
