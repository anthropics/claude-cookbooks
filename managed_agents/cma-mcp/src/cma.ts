import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic();

if (!process.env.CLAUDE_ENVIRONMENT_ID) {
  throw new Error("CLAUDE_ENVIRONMENT_ID is required");
}
const ENVIRONMENT_ID: string = process.env.CLAUDE_ENVIRONMENT_ID;

/** Hard cap on events returned by listEvents to prevent memory exhaustion. */
const MAX_EVENTS = 500;

// --- error wrapper --------------------------------------------------------

/** Wrap API calls so internal details never leak to the MCP client. */
async function safe<T>(label: string, fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    console.error(`[cma] ${label}:`, err);
    throw new Error(`CMA error in ${label} — check server logs for details`);
  }
}

// --- types ----------------------------------------------------------------

interface SessionEvent {
  id: string;
  type: string;
  processed_at?: string;
  content?: Array<{ type: string; text?: string }>;
  name?: string;
  input?: unknown;
  is_error?: boolean;
  stop_reason?: { type: string };
}

interface StreamEvent extends SessionEvent {
  content?: Array<{ type: string; text?: string }>;
  name?: string;
  stop_reason?: { type: string };
}

// --- Tier 1: 1:1 endpoint wrappers ----------------------------------------

export async function listAgents(opts: { limit?: number; name_contains?: string } = {}) {
  return safe("listAgents", async () => {
    const limit = opts.limit ?? 50;
    const needle = opts.name_contains?.toLowerCase();
    const out: Array<{ id: string; name: string; description: string | null; model: string }> = [];
    for await (const a of anthropic.beta.agents.list()) {
      if (needle && !a.name.toLowerCase().includes(needle)) continue;
      out.push({
        id: a.id,
        name: a.name,
        description: a.description ?? null,
        model: typeof a.model === "string" ? a.model : a.model.id,
      });
      if (out.length >= limit) break;
    }
    return out;
  });
}

export async function getAgent(agent_id: string) {
  return safe("getAgent", async () => {
    const a = await anthropic.beta.agents.retrieve(agent_id);
    // Return safe fields only — system prompts, tool configs, and MCP server
    // URLs are deliberately excluded to prevent information disclosure.
    return {
      id: a.id,
      name: a.name,
      description: a.description ?? null,
      model: typeof a.model === "string" ? a.model : a.model.id,
      created_at: a.created_at,
    };
  });
}

export async function createSession(agent_id: string, title?: string) {
  return safe("createSession", async () => {
    const session = await anthropic.beta.sessions.create({
      agent: agent_id,
      environment_id: ENVIRONMENT_ID,
      ...(title ? { title } : {}),
    });
    return { session_id: session.id, status: session.status };
  });
}

export async function sendMessage(session_id: string, text: string) {
  return safe("sendMessage", async () => {
    await anthropic.beta.sessions.events.send(session_id, {
      events: [{ type: "user.message", content: [{ type: "text", text }] }],
    });
    return { queued: true };
  });
}

export async function interrupt(session_id: string) {
  return safe("interrupt", async () => {
    await anthropic.beta.sessions.events.send(session_id, {
      events: [{ type: "user.interrupt" }],
    });
    return { queued: true };
  });
}

export async function getSession(session_id: string) {
  return safe("getSession", async () => {
    const s = await anthropic.beta.sessions.retrieve(session_id);
    return {
      id: s.id,
      status: s.status,
      title: s.title,
      agent: s.agent,
      created_at: s.created_at,
      updated_at: s.updated_at,
      usage: s.usage,
    };
  });
}

export async function listEvents(session_id: string, after_id?: string) {
  return safe("listEvents", async () => {
    const events: ReturnType<typeof summarizeEvent>[] = [];
    let skip = Boolean(after_id);
    for await (const e of anthropic.beta.sessions.events.list(session_id)) {
      if (skip) {
        if (e.id === after_id) skip = false;
        continue;
      }
      events.push(summarizeEvent(e as SessionEvent));
      if (events.length >= MAX_EVENTS) break;
    }
    return { events, truncated: events.length >= MAX_EVENTS };
  });
}

export async function archiveSession(session_id: string) {
  return safe("archiveSession", async () => {
    await anthropic.beta.sessions.archive(session_id);
    return { archived: true };
  });
}

// --- Tier 1.5: the one convenience verb -----------------------------------

/**
 * Stream session events until the agent goes idle (or terminates, or timeout).
 * Collects agent.message text into `reply`. This is the SSE→request/response
 * shim MCP needs — the only place we editorialize over the raw API.
 */
export async function waitForIdle(session_id: string, timeout_sec = 120) {
  return safe("waitForIdle", async () => {
    const deadline = Date.now() + timeout_sec * 1000;
    const replyParts: string[] = [];
    const activity: string[] = [];
    let status: "idle" | "terminated" | "timeout" | "requires_action" = "timeout";
    let last_event_id: string | undefined;

    const stream = await anthropic.beta.sessions.events.stream(session_id);
    try {
      for await (const e of stream as AsyncIterable<StreamEvent>) {
        last_event_id = e.id;
        if (e.type === "agent.message") {
          for (const b of e.content ?? []) {
            if (b.type === "text" && b.text) replyParts.push(b.text);
          }
        } else if (e.type === "agent.tool_use" || e.type === "agent.mcp_tool_use") {
          activity.push(`→ ${e.name}`);
        } else if (e.type === "session.status_idle") {
          status =
            e.stop_reason?.type === "requires_action" ? "requires_action" : "idle";
          break;
        } else if (e.type === "session.status_terminated") {
          status = "terminated";
          break;
        }
        if (Date.now() > deadline) break;
      }
    } finally {
      // Close the SSE connection so it doesn't linger.
      const s = stream as unknown as Record<string, unknown>;
      if (typeof s.close === "function") {
        (s.close as () => void)();
      } else if (
        s.controller &&
        typeof (s.controller as AbortController).abort === "function"
      ) {
        (s.controller as AbortController).abort();
      }
    }

    return {
      status,
      reply: replyParts.join("").trim(),
      tool_activity: activity,
      last_event_id,
    };
  });
}

// --- helpers --------------------------------------------------------------

function summarizeEvent(e: SessionEvent) {
  const base = { id: e.id, type: e.type, processed_at: e.processed_at };
  if (e.type === "agent.message") {
    return {
      ...base,
      text: (e.content ?? [])
        .filter((b) => b.type === "text")
        .map((b) => b.text ?? "")
        .join(""),
    };
  }
  if (e.type === "agent.tool_use" || e.type === "agent.mcp_tool_use") {
    // Redact tool inputs — they may contain credentials, PII, or file contents.
    return { ...base, name: e.name };
  }
  if (e.type === "agent.tool_result" || e.type === "agent.mcp_tool_result") {
    return { ...base, is_error: e.is_error };
  }
  if (e.type === "session.status_idle") {
    return { ...base, stop_reason: e.stop_reason };
  }
  return base;
}
