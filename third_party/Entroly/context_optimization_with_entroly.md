# Context Optimization with Entroly

This guide shows how to use [Entroly](https://github.com/juyterman1000/entroly) to reduce context size before sending prompts to Claude, while keeping omitted content exactly recoverable.

## What is Entroly?

Entroly is a local-first context-control plane that selects the most relevant code fragments under an explicit token budget. Unlike lossy compression, Entroly uses content-addressed handles (CCR) to keep every omitted fragment byte-exactly recoverable — nothing is permanently lost.

## Prerequisites

```bash
pip install entroly anthropic
```

Requires Python 3.10+. No Entroly API key needed — all operations run locally.

## Quick verification

Before using Entroly with Claude, verify it works locally (no API key, no network calls):

```bash
entroly verify-claims
```

Expected output: **12/12 checks passed**.

## Usage: SDK Integration

### 1. Compress messages before sending to Claude

```python
import anthropic
from entroly import compress_messages

client = anthropic.Anthropic()

# Original messages with large context
messages = [
    {
        "role": "user",
        "content": f"Given this codebase:\n\n{large_codebase_text}\n\nHow does authentication work?"
    }
]

# Compress: select relevant fragments under a token budget
compressed_messages, receipt = compress_messages(
    messages,
    budget=8000,  # max tokens for context
    return_receipt=True
)

# Send compressed messages to Claude
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=compressed_messages
)

print(response.content[0].text)
```

### 2. Inspect the Context Receipt

```python
# The receipt shows what was included and excluded
print(f"Original tokens: {receipt.original_tokens}")
print(f"Selected tokens: {receipt.selected_tokens}")
print(f"Fragments included: {receipt.included_count}")
print(f"Fragments excluded: {receipt.excluded_count}")

# Each excluded fragment has a CCR handle for recovery
for excluded in receipt.excluded:
    print(f"  Excluded: {excluded.path} → handle: {excluded.ccr_handle}")
```

### 3. Recover excluded content

```python
from entroly import recover

# If Claude's response references something that was excluded,
# recover it by CCR handle
content = recover("ccr:811e14e88963b07f71a564a1")
print(content)  # Exact original bytes restored
```

## Usage: Transparent Proxy

For zero-code-change integration, use Entroly as a proxy:

```bash
# Start the proxy
entroly proxy --budget 8000

# Point your Claude client at the proxy
export ANTHROPIC_BASE_URL=http://localhost:9377/v1
python your_existing_script.py  # No code changes needed
```

## Usage: MCP Server

For Claude Code or any MCP-compatible client:

```json
{
  "mcpServers": {
    "entroly": {
      "command": "python",
      "args": ["-m", "entroly"],
      "env": { "ENTROLY_BUDGET": "8000" }
    }
  }
}
```

## Measuring savings locally

Before connecting to a paid model, measure potential savings on your codebase:

```bash
entroly simulate --path ./your-project
```

Example output:
```
Indexed 140 files, 620,162 estimated tokens
Query: "How does authentication work?"
  Selected: 3,877 tokens (87.9% fewer than 32k baseline)
  Note: local estimate only. No LLM call made. Quality not evaluated.
```

## Honest limitations

| Aspect | Detail |
|--------|--------|
| Savings | **Workload-dependent** — varies by codebase size and query |
| Quality | SQuAD accuracy drops 80% → 72% at 43.8% savings |
| Small repos | Codebases that fit the context window pass through unchanged |
| Billing | `entroly simulate` gives token estimates, not provider billing guarantees |
| Provider cache | Real-world savings depend on provider cache behavior |

Full limitations: [docs/limitations.md](https://github.com/juyterman1000/entroly/blob/main/docs/limitations.md)

## Learn more

- [Entroly GitHub](https://github.com/juyterman1000/entroly) — Apache-2.0
- [PyPI](https://pypi.org/project/entroly/) — `pip install entroly`
- [Documentation](https://github.com/juyterman1000/entroly/tree/main/docs)

---

*Disclosure: This guide was contributed by the Entroly maintainer.*
