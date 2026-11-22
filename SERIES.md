# Claude Code 101 — the series

> *"You drop into a large, unfamiliar, professional codebase you didn't write....."*

This fork of [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) is the working codebase for the **30 Days Building with Claude — Claude Code 101** video series, taught from a Forward Deployed Engineer's point of view and following the [Claude Code 101](https://academy.claude.com/courses/claude-code-101) course on Claude Academy.

Every episode points at an exact tag, so you can follow along from the same state you see on screen:

```bash
git clone https://github.com/Ikurira/claude-cookbooks
cd claude-cookbooks
git checkout <episode-tag>     # e.g. lf3-start
```

## Conventions

| Ref | Meaning |
|---|---|
| `series-base` | Pinned baseline of the upstream repo every episode starts from |
| `sNN-start` / `sNN-end` | Short NN — state before / after |
| `lfN-start` / `lfN-end` | Long-form video N — state before / after |
| `ikurira/<episode-topic>` branches | Live work recorded in an episode; merged to `main` after recording |

## Episodes

| Episode | Lesson | Start | End | Video |
|---|---|---|---|---|
| LF1 — What Claude Code actually is: the agentic loop, live | 1–2 | `lf1-start` | `lf1-end` | _coming soon_ |
| LF2 — Install it, pick your oversight: the 4 permission modes | 3–4 | `lf2-start` | `lf2-end` | _coming soon_ |
| LF3 — Explore → Plan → Code → Commit on a real codebase | 5–7 | `lf3-start` | `lf3-end` | _coming soon_ |
| LF4 — Make it yours: CLAUDE.md, subagents, skills, MCP, hooks | 8–12 | `lf4-start` | `lf4-end` | _coming soon_ |

Shorts are added to this table as they are published.

The cookbook content itself is unchanged and remains © Anthropic under the MIT License (see `LICENSE`).
