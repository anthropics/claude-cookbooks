# Claude Cookbooks

A collection of Jupyter notebooks and Python examples for building with the Claude API.

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Set up API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Development Commands

```bash
make format        # Format code with ruff
make lint          # Run linting
make check         # Run format-check + lint
make fix           # Auto-fix issues + format
make test          # Run pytest
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
- **Formatter:** Ruff

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

1. **API Keys:** Never commit `.env` files. Always use `os.environ.get("ANTHROPIC_API_KEY")`

2. **Dependencies:** Use `uv add <package>` or `uv add --dev <package>`. Never edit pyproject.toml directly.

3. **Models:** Use current Claude models. Check docs.anthropic.com for latest versions.
   - Sonnet: `claude-sonnet-4-5-20250929`
   - Haiku: `claude-haiku-4-5-20251001`

4. **Notebooks:**
   - Keep outputs in notebooks (intentional for demonstration)
   - One concept per notebook
   - Test that notebooks run top-to-bottom without errors

5. **Quality checks:** Run `make check` before committing. Pre-commit hooks validate formatting and notebook structure.

## Slash Commands

These commands are available in Claude Code and CI:

- `/notebook-review` - Review notebook quality
- `/model-check` - Validate Claude model references
- `/link-review` - Check links in changed files

## Project Structure

```
capabilities/      # Core Claude capabilities (RAG, classification, etc.)
skills/            # Advanced skill-based notebooks
tool_use/          # Tool use and integration patterns
multimodal/        # Vision and image processing
misc/              # Batch processing, caching, utilities
third_party/       # Pinecone, Voyage, Wikipedia integrations
extended_thinking/ # Extended reasoning patterns
scripts/           # Validation scripts
.claude/           # Claude Code commands and skills
```

## Adding a New Cookbook

1. Create notebook in the appropriate directory
2. Add entry to `registry.yaml` with title, description, path, authors, categories
3. Add author info to `authors.yaml` if new contributor
4. Run quality checks and submit PR
