#!/usr/bin/env bun
// Streamable HTTP transport — for claude.ai web Connectors (or any remote MCP client).
// Web-standard Request/Response, so this same file runs on Bun, Node 18+, Deno,
// and (with env plumbing) Cloudflare Workers.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { timingSafeEqual } from "node:crypto";
import { registerTools } from "./tools";

const TOKEN = process.env.CMA_MCP_TOKEN;
if (!TOKEN) throw new Error("CMA_MCP_TOKEN is required for the HTTP server");
const PORT = Number(process.env.PORT) || 3000;

// --- request size limit ----------------------------------------------------

/** Max request body size (1 MB). Rejects oversized payloads before parsing. */
const MAX_BODY_BYTES = 1_048_576;

// --- in-memory rate limiter ------------------------------------------------

const RATE_WINDOW_MS = 60_000; // 1 minute
const RATE_MAX_REQUESTS = 60;  // per window

interface RateBucket {
  count: number;
  resetAt: number;
}

const rateBuckets = new Map<string, RateBucket>();

/** Prune expired buckets every 5 minutes to prevent memory growth. */
setInterval(() => {
  const now = Date.now();
  for (const [key, bucket] of rateBuckets) {
    if (bucket.resetAt <= now) rateBuckets.delete(key);
  }
}, 300_000).unref();

function isRateLimited(key: string): boolean {
  const now = Date.now();
  let bucket = rateBuckets.get(key);
  if (!bucket || bucket.resetAt <= now) {
    bucket = { count: 0, resetAt: now + RATE_WINDOW_MS };
    rateBuckets.set(key, bucket);
  }
  bucket.count++;
  return bucket.count > RATE_MAX_REQUESTS;
}

// --- transport factory -----------------------------------------------------

// Stateless mode (no sessionIdGenerator): each HTTP request gets its own
// McpServer + transport. Fine because the tools themselves are stateless —
// Claude holds the CMA session_id across turns.
function newTransport() {
  const server = new McpServer({ name: "cma-mcp", version: "0.1.0" });
  registerTools(server);
  const transport = new WebStandardStreamableHTTPServerTransport({});
  server.connect(transport);
  return transport;
}

// --- auth ------------------------------------------------------------------

function authorized(req: Request): boolean {
  const provided = req.headers.get("authorization") ?? "";
  const expected = `Bearer ${TOKEN}`;
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

// --- server ----------------------------------------------------------------

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/health" && req.method === "GET") {
      return new Response("ok");
    }
    if (url.pathname !== "/mcp") {
      return new Response("Not Found", { status: 404 });
    }

    // The only thing standing between the internet and your ANTHROPIC_API_KEY's
    // CMA quota. Do not remove.
    if (!authorized(req)) {
      return new Response("Unauthorized", { status: 401 });
    }

    // Rate limit — keyed on client IP (falls back to "unknown" behind proxies
    // without X-Forwarded-For).
    const clientIp = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
    if (isRateLimited(clientIp)) {
      return new Response("Too Many Requests", {
        status: 429,
        headers: { "Retry-After": String(Math.ceil(RATE_WINDOW_MS / 1000)) },
      });
    }

    // Reject oversized request bodies.
    const contentLength = Number(req.headers.get("content-length") ?? "0");
    if (contentLength > MAX_BODY_BYTES) {
      return new Response("Payload Too Large", { status: 413 });
    }

    return newTransport().handleRequest(req);
  },
});

console.error(`[cma-mcp] HTTP server on :${PORT}/mcp`);
