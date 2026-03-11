# Claude Cookbooks

A collection of Jupyter notebooks and Python examples for building with the Claude API.

## Quick Start

```bash
# Install dependencies (Python 3.11–3.12 required)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Set up API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Development Commands

```bash
make format              # Format code with ruff
make lint                # Run linting
make check               # Run format-check + lint
make fix                 # Auto-fix issues + format
make test                # Run pytest
make clean               # Remove cache files
make sort-authors        # Sort authors.yaml alphabetically
```

Or directly with uv:

```bash
uv run ruff format .           # Format
uv run ruff check .            # Lint
uv run ruff check --fix .      # Auto-fix
uv run pre-commit run --all-files
```

## Code Style

- **Line length:** 100 characters
- **Quotes:** Double quotes
- **Formatter:** Ruff (v0.14+)
- **Linting rules:** E, F, I, W, UP, S, B

Notebooks have relaxed rules for mid-file imports (E402), redefinitions (F811), and variable naming (N803, N806).

## Git Workflow

**Branch naming:** `<username>/<feature-description>`

**Commit format (conventional commits):**
```
feat(scope): add new feature
fix(scope): fix bug
docs(scope): update documentation
style: lint/format
```

## Key Rules

1. **API Keys:** Never commit `.env` files. Always use `os.environ.get("ANTHROPIC_API_KEY")` with `dotenv.load_dotenv()`. Never hardcode secrets.

2. **Dependencies:** Use `uv add <package>` or `uv add --dev <package>`. Never edit pyproject.toml directly.

3. **Models:** Use current Claude models. Check docs.anthropic.com for latest versions.
   - Sonnet: `claude-sonnet-4-6`
   - Haiku: `claude-haiku-4-5`
   - Opus: `claude-opus-4-6`
   - **Never use dated model IDs** (e.g., `claude-sonnet-4-6-20250514`). Always use the non-dated alias.
   - Define a `MODEL` constant at the top of each notebook for easy updates.
   - **Bedrock model IDs** follow a different format. Use the base Bedrock model ID from the docs:
     - Opus 4.6: `anthropic.claude-opus-4-6-v1`
     - Sonnet 4.5: `anthropic.claude-sonnet-4-5-20250929-v1:0`
     - Haiku 4.5: `anthropic.claude-haiku-4-5-20251001-v1:0`
     - Prepend `global.` for global endpoints (recommended): `global.anthropic.claude-opus-4-6-v1`
     - Note: Bedrock models before Opus 4.6 require dated IDs in their Bedrock model ID.

4. **Notebooks:**
   - Keep outputs in notebooks (intentional for demonstration)
   - One concept per notebook
   - Test that notebooks run top-to-bottom without errors
   - Use `%%capture` for pip install cells to hide noisy output
   - Structure: introduction → prerequisites → sections with explanatory text before and after code → conclusion

5. **Quality checks:** Run `make check` before committing. Pre-commit hooks automatically validate formatting and notebook structure.

## Pre-commit Hooks

The following hooks run automatically on `git commit`:
- **ruff-check** – Lints Python and Jupyter files with auto-fix
- **ruff-format** – Formats Python and Jupyter files
- **validate-notebooks** – Validates notebook structure (`scripts/validate_notebooks.py`)
- **validate-authors-sorted** – Ensures `authors.yaml` is alphabetically sorted

## Testing

### Notebook tests

```bash
make test-notebooks                          # Structure tests (fast, no API calls)
make test-notebooks-exec                     # Execution tests (slow, requires API key)
make test-notebooks-tox                      # Isolated tox environment
make test-notebooks-quick                    # Quick validation without pytest

# Target a specific notebook or directory:
make test-notebooks NOTEBOOK=tool_use/calculator_tool.ipynb
make test-notebooks NOTEBOOK_DIR=capabilities
```

### Tox environments

| Environment | Purpose | API key required |
|-------------|---------|-----------------|
| `structure` | Structural validation, no execution | No |
| `structure-single` | Single notebook structural test | No |
| `execution` | Full execution (timeout: 300s) | Yes |
| `execution-single` | Single notebook execution | Yes |
| `registry` | Only notebooks listed in registry.yaml | No |
| `quick` | Smoke test on `capabilities/` | No |
| `third-party` | Third-party integration notebooks | Yes + provider keys |
| `lint` / `format` | Code quality checks | No |

Run a specific environment:
```bash
uv run tox -e structure
uv run tox -e execution-single -- tool_use/calculator_tool.ipynb
```

### Environment variables for execution tests

```
ANTHROPIC_API_KEY   # Required for execution tests
OPENAI_API_KEY      # Optional, for OpenAI integrations
VOYAGE_API_KEY      # Optional, for Voyage embeddings
PINECONE_API_KEY    # Optional, for Pinecone integrations
MONGODB_URI         # Optional, for MongoDB integrations
DEEPGRAM_API_KEY    # Optional, for Deepgram integrations
ELEVENLABS_API_KEY  # Optional, for ElevenLabs integrations
WOLFRAM_APP_ID      # Optional, for Wolfram integrations
```

## Slash Commands

These commands are available in Claude Code and CI:

- `/notebook-review` – Review notebook quality and structure
- `/model-check` – Validate Claude model references
- `/link-review` – Check links in changed files
- `/review-pr` – Full PR code review
- `/review-pr-ci` – CI-automated PR review
- `/review-issue` – Review a GitHub issue
- `/add-registry` – Add a notebook to registry.yaml

The `code-reviewer` subagent (`.claude/agents/code-reviewer.md`) is invoked automatically after significant code changes to perform thorough code reviews.

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `notebook-tests.yml` | PR changes, push to main | Structure + execution tests on changed notebooks |
| `lint-format.yml` | PR/push with .py/.ipynb | Ruff formatting and linting checks |
| `notebook-quality.yml` | Notebook changes | Quality score and structure validation |
| `verify-authors.yml` | authors.yaml changes | Author validation and sorting |
| `claude-pr-review.yml` | PR opened/updated | Claude-powered code review |
| `claude-model-check.yml` | PR changes | Validates Claude model usage |
| `claude-link-review.yml` | PR changes | Link validation in docs |
| `notebook-diff-comment.yml` | PR with notebook changes | Posts diff summary |
| `links.yml` | Scheduled + PR | Link checking with lychee |

## Project Structure

```
capabilities/      # Core Claude capabilities (RAG, classification, summarization, text-to-SQL)
claude_agent_sdk/  # Agent SDK examples
coding/            # Coding-specific patterns
extended_thinking/ # Extended reasoning patterns
finetuning/        # Fine-tuning guides
misc/              # Batch processing, caching, evals, utilities
multimodal/        # Vision and image processing
observability/     # Observability and monitoring patterns
patterns/          # Agent workflow patterns (orchestrator, evaluator)
skills/            # Claude skills documentation
third_party/       # Pinecone, LlamaIndex, MongoDB, Deepgram, ElevenLabs, Wikipedia, Wolfram
tool_evaluation/   # Tool evaluation patterns
tool_use/          # Tool use and integration examples
scripts/           # Validation and testing scripts
tests/             # Test suite (pytest)
.claude/           # Claude Code commands, agents, and skills
  commands/        # Slash commands (notebook-review, model-check, etc.)
  agents/          # Subagents (code-reviewer)
  skills/          # Skills (cookbook-audit)
.github/workflows/ # CI/CD workflows
```

## Adding a New Cookbook

1. Create notebook in the appropriate directory
2. Add entry to `registry.yaml` with title, description, path, authors, categories
3. Add author info to `authors.yaml` if new contributor (keep alphabetically sorted)
4. Run quality checks: `make check && make test-notebooks`
5. Submit PR

### Notebook structure requirements

A well-formed notebook must include:
- **Introduction** – Problem hook and learning objectives
- **Prerequisites** – Required knowledge, tools, and setup (API key, installs)
- **Sections** – Explanatory text *before* and *after* each code block
- **Conclusion** – Summary that maps back to learning objectives

Use `%%capture` for install cells. Load env vars with `dotenv.load_dotenv()`, not `os.environ` directly.

### registry.yaml fields

```yaml
- title: "Notebook Title"
  description: "What problem this solves"
  path: "directory/notebook.ipynb"
  authors:
    - github_username
  date: "YYYY-MM-DD"
  categories:
    - Category1
    - Category2
```
