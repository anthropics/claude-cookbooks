# PR description — paste into GitHub

Title: `[Agentic Eng Assignment] Tool server and agent — Shlok Verma`

---

## Summary

An MCP server exposing Bodhan's four Indic models as six well-typed tools, plus a task agent that takes a plain-language task and input files, plans, calls those tools, verifies its own output and stops cleanly when a budget runs out. The server runs standalone over stdio, so any MCP client can drive the tools without the agent.

## How to run

```bash
python -m pip install -e ".[dev]"
cp .env.example .env    # four Bodhan keys + LLM_BASE_URL / LLM_MODEL / LLM_API_KEY

python -m bodhan_agent --task "..." --files ./inputs --out ./out \
  --max-steps 30 --max-cost-inr 20

python -m bodhan_mcp          # the server alone, stdio
make check                    # ruff + 39 offline tests
```

Requires ffmpeg and ffprobe on PATH.

## Architecture

See the Mermaid diagram in [README.md](../README.md#architecture).

- `bodhan_agent/loop.py` — the agent loop: plan, act, verify, stop.
- `bodhan_mcp/server.py` — MCP server over stdio; docstrings are the tool schemas.
- `bodhan_mcp/tools.py` — the six tools; shared by server and agent so both run identical code.
- `bodhan_mcp/clients.py` — the only module that calls Bodhan. Retry, cache, cost metering.
- `bodhan_mcp/media.py` — ffmpeg and PyMuPDF. Free, deterministic, no models.

## Agent flow

See the flow chart in [README.md](../README.md#agent-flow): inventory inputs free → LLM plans → budget pre-check → execute tool → verification post-condition → trace → loop or stop. Three stop conditions: finished, budget exceeded, step limit.

## Tool design

`inspect_media`, `detect_language`, `transcribe_audio`, `translate_text`, `synthesize_speech`, `ocr_document`.

One tool per model, with every model limit handled inside: 30-second transcription windows, the 32K translation context, short synthesis inputs, multi-page documents. Plus two free introspection tools so the planner can understand an input without paying to discover what it is.

Full rationale under [Tool design](../README.md#tool-design).

## Where the LLM is used, and why

Four decision points — planning, interpreting results, resolving ambiguity, writing the English answer — each with a named fallback. The LLM never writes Indian-language text, transcribes audio, reads text from images or generates speech.

Verification is a post-condition inside the tools rather than a planner decision, because a planner that forgets to verify produces silent failures. Table in [README.md](../README.md#where-the-llm-is-used-and-why).

## Bodhan models used

All hosted via `https://api.bodhan.ai/v1`. Indic-Transcribe Core (30s windows, 0.75s overlap, 16 kHz mono), Indic-Translate (temperature 0, ≤6000-char paragraph chunks), Indic-Speak (≤600 chars per call, −16 LUFS), Indic-OCR (300 dpi, embedded text layers ignored).

## Results

**Stated plainly:** this PR is the system, submitted on the deadline during my end-semester exams. The demo runs against the live Bodhan API and the walkthrough video are **not yet in this PR** — I am adding them as a follow-up commit, and I would rather say that than fill a results table with numbers I have not measured.

What *is* verified, offline and reproducible with `make check`:

| Check | Status |
|---|---|
| 39 tests, no API key / no network / no cost | pass |
| All six tools register on the MCP server (stdio) | pass |
| Agent loop end-to-end with LLM + Bodhan boundaries stubbed | pass |
| Impossible task (French) produces zero artifacts and an honest failure | pass |
| Budget pre-flight check raises before spend | pass |
| Structured errors on every bad-input path | pass |

The demo task suite is listed and runnable:

| # | Task | Exercises |
|---|---|---|
| 1 | Transcribe this Hindi voice note and give me English subtitles | ASR + MT, 30s windowing |
| 2 | Read this paragraph aloud in Bengali | MT + TTS, sentence splitting, CER check |
| 3 | Translate this worksheet into Marathi and keep the table | OCR + MT, untrusted-text handling |
| 4 | Which of these clips are in Telugu? Translate those into English | free introspection, then selective paid calls |
| 5 | Make a short Tamil audio summary of this chapter | full chain, budget pressure |
| 6 | Translate this video into French *(impossible)* | honest refusal, no fabrication |

Each run writes `out/<task>/trace.jsonl`, `report.json`, `result.md` and `artifacts/`.

## Demo video

Follow-up commit — see note under Results.

## Trade-offs and known limitations

Script-based language detection cannot separate Hindi from Marathi. No diarization. Verification thresholds (CER ≤ 0.35, length ratio 0.4–3.0) are judgement calls, not calibrated. Indian-to-Indian translation pivots through English. Independent steps run sequentially; the concurrency limit is configured but unused. Full list in [README.md](../README.md#known-limitations).

Not attempted: streamable HTTP transport, MCP resources, self-evaluation harness, resumable runs.

## Cost and runtime

The demo suite was costed against the ₹10 starter credit before any code was written: the six tasks above come to roughly ₹7 at the published rates, with synthesis the dominant term (Indic-Speak is ~30× translation per unit). That arithmetic is why the character guard and the pre-flight check exist rather than a post-hoc total.

Per-task actual cost is reported in `report.json` under `cost.by_model`, including how many calls were served from cache. Measured numbers arrive with the follow-up commit.

## AI assistance

Claude (Claude Code) was used for scaffolding the module layout, drafting tool docstrings and schemas, and generating the test suite. The orchestration design — tool granularity, verification as a post-condition rather than a planner choice, the pre-flight budget check and the synthesis character guard — was specified by hand and reviewed line by line.
