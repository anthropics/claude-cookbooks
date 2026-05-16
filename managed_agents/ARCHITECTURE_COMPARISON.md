# Managed Agents Cookbooks — Architectural Comparison

Two cookbooks, two integration patterns, one underlying API: Claude Managed Agents (CMA).

## At a Glance

- **CMA-MCP**: Synchronous relay — a human types in Claude Desktop/web, an MCP server proxies each turn to a hosted CMA agent, and the reply comes back in the same request.
- **Linear Bridge**: Asynchronous webhook bridge — a Linear @mention triggers a CMA session; when the agent finishes, a second webhook delivers the reply back to the Linear issue.

## Integration Pattern

### CMA-MCP — Request/Response Relay

```
User → Claude Desktop/Web → MCP tool call → CMA Sessions API → Agent runs → SSE stream → Reply
```

- The MCP server is a **stateless proxy** between a Claude client and the CMA API.
- Each user turn maps to `send_message` → `wait_for_idle` (blocks on SSE until the agent is done).
- `session_id` is the only state, held by the calling Claude instance — the server stores nothing.
- The `wait_for_idle` shim is the key design choice: MCP is request/response, but CMA completion is SSE. This tool bridges that gap by streaming internally and returning once idle.

### Linear Bridge — Dual-Webhook Event Bridge

```
Linear @mention → POST /linear-webhook → CMA sessions.create → Agent runs on Anthropic infra
                                                                         │
Anthropic session.status_idled → POST /cma-webhook → sessions.retrieve → Linear comment
```

- The bridge is a **stateless translator** between two event-driven systems that share no wire format or credentials.
- Routing state lives in CMA session `metadata` (`linear_session_id`, `linear_org_id`) — not in the bridge process.
- Fire-and-forget on the inbound side; pull-on-signal on the outbound side (the idle webhook is a doorbell, not a delivery — the bridge retrieves the actual content).

## Statelessness

Both are stateless, but achieve it differently:

- **CMA-MCP**: The *client* (Claude Desktop) holds `session_id` across turns. The server is a pure function: input → API call → output.
- **Linear Bridge**: CMA session `metadata` holds routing state. The bridge reads it back on the return path. No client holds anything; no process memory is required.

## Transport

- **CMA-MCP**: Two transports for one tool set — stdio (Claude Desktop spawns it as a subprocess) and Streamable HTTP (claude.ai connects over the network with bearer auth). Same `tools.ts`, different entrypoints.
- **Linear Bridge**: Standard HTTP webhook receiver. Two inbound routes (`/linear-webhook`, `/cma-webhook`), plus OAuth endpoints for one-time setup.

## Synchronicity

- **CMA-MCP**: Synchronous from the user's perspective. `wait_for_idle` blocks the tool call until the agent finishes (with configurable timeout and resume via `last_event_id`).
- **Linear Bridge**: Fully asynchronous. The inbound webhook returns immediately after creating the CMA session. Minutes later, the idle webhook arrives and the reply is posted. The user sees "Thinking..." in Linear while the agent works.

## Authentication

- **CMA-MCP**: `ANTHROPIC_API_KEY` baked into server config; optional bearer token gates the HTTP transport. All CMA usage bills to the server's key, not the end user's.
- **Linear Bridge**: Three credential sets — `ANTHROPIC_API_KEY` for CMA, Linear OAuth token (`actor=app`) for posting replies, and webhook signing secrets on both sides for payload verification.

## Error Handling

- **CMA-MCP**: Timeout-and-resume — `wait_for_idle` returns `status: "timeout"` with `last_event_id` so the client can call again without losing progress. Destructive operations are excluded by design.
- **Linear Bridge**: 10-second ack rule (post a "Thinking..." activity immediately); idempotency via `event.id` dedup; workspace-scoped filtering to ignore unrelated sessions; graceful 204 for non-matching webhooks.

## Extensibility

- **CMA-MCP**: Add a tool by mapping a CMA endpoint in `cma.ts` and registering it in `tools.ts`. Intentionally excludes destructive ops (agent delete, vault access, environment management).
- **Linear Bridge**: Six documented extensions — GitHub repo mounting, MCP tools on the agent, outcome rubrics, multiagent coordination, memory stores, and custom host-side tools. All configured via `sessions.create` or agent definition parameters.

## When to Use Which

- **CMA-MCP** when you want interactive, conversational access to hosted agents from Claude Desktop or claude.ai — the agent is a tool the user chats with.
- **Linear Bridge** when you want event-driven automation — the agent reacts to external triggers (issue mentions) and posts results without a human in the loop.

## Shared Foundations

Both cookbooks share:
- `@anthropic-ai/sdk` ≥ 0.95.1 (CMA beta API)
- Bun as the runtime
- A `skill.md` with setup walkthrough, gotchas, and debugging tables
- A `CLAUDE.md` that teaches Claude how to help set up and extend the project
- Minimal code (~150–200 LOC of logic each)
