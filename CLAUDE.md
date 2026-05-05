# Claude Cookbooks

A collection of Jupyter notebooks and Python examples for building with the Claude API. These cookbooks provide copyable code snippets and patterns that developers can integrate into their projects.

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
make clean         # Remove cache files
make sort-authors  # Sort authors.yaml alphabetically
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
- **Python version:** 3.11+

Notebooks have relaxed rules for mid-file imports (E402), redefinitions (F811), and variable naming (N803, N806).

## Git Workflow

**Branch naming:** `<username>/<feature-description>`

**Commit format (conventional commits):**
```
feat(scope): add new feature
fix(scope): fix bug
docs(scope): update documentation
style: lint/format
refactor: code restructuring
test: add tests
chore: maintenance
ci: CI/CD changes
```

## Key Rules

1. **API Keys:**
   - Never commit `.env` files
   - Use `dotenv.load_dotenv()` instead of `os.environ` directly
   - Define API key access pattern: `os.environ.get("ANTHROPIC_API_KEY")`
1. **API Keys:** Never commit `.env` files. Use `dotenv.load_dotenv()` then access keys via `os.environ` or `os.getenv()`

2. **Dependencies:**
   - Use `uv add <package>` or `uv add --dev <package>`
   - Never edit pyproject.toml directly

3. **Models:** Use current Claude models. Check docs.anthropic.com for latest versions.
   - Sonnet: `claude-sonnet-4-5-20250929`
   - Haiku: `claude-haiku-4-5-20251001`
   - Opus: `claude-opus-4-5-20251101`
   - Define model as a `MODEL` constant at the top of notebooks
   - Sonnet: `claude-sonnet-4-6`
   - Haiku: `claude-haiku-4-5`
   - Opus: `claude-opus-4-6`
   - **Never use dated model IDs** (e.g., `claude-sonnet-4-6-20250514`). Always use the non-dated alias.
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
   - Use `%%capture` for pip install to suppress output
   - Explain before code blocks (what we're doing) and after (what we learned)

5. **Quality checks:**
   - Run `make check` before committing
   - Pre-commit hooks validate formatting and notebook structure

## Slash Commands

These commands are available in Claude Code and CI:

| Command | Description |
|---------|-------------|
| `/notebook-review` | Comprehensive notebook quality review |
| `/model-check` | Validate Claude model references are current |
| `/link-review` | Check links in changed files for issues |
| `/add-registry` | Add a new notebook to registry.yaml |
| `/review-pr` | Review an open pull request |
| `/review-pr-ci` | Review a PR for CI (automated use) |
| `/review-issue` | Review and respond to a GitHub issue |

## Skills

| Skill | Description |
|-------|-------------|
| `cookbook-audit` | Comprehensive audit of notebook quality using style guide rubrics |

## Project Structure

```
.claude/                    # Claude Code configuration
├── agents/                 # Custom agent definitions
├── commands/               # Slash command definitions
└── skills/                 # Skill definitions (cookbook-audit)

capabilities/               # Core Claude capabilities
├── classification/         # Text and data classification
├── contextual-embeddings/  # Contextual retrieval with embeddings
├── retrieval_augmented_generation/  # RAG patterns
├── summarization/          # Text summarization techniques
└── text_to_sql/            # Natural language to SQL

claude_agent_sdk/           # Claude Agent SDK tutorials
├── 00_The_one_liner_research_agent.ipynb
├── 01_The_chief_of_staff_agent.ipynb
├── 02_The_observability_agent.ipynb
├── chief_of_staff_agent/   # Multi-agent system example
├── observability_agent/    # MCP server integration example
└── research_agent/         # Research agent example

coding/                     # Code-related notebooks
└── prompting_for_frontend_aesthetics.ipynb

extended_thinking/          # Extended reasoning patterns
├── extended_thinking.ipynb
└── extended_thinking_with_tool_use.ipynb

finetuning/                 # Fine-tuning guides
└── finetuning_on_bedrock.ipynb

misc/                       # Utilities and miscellaneous
├── batch_processing.ipynb      # Message Batches API
├── building_evals.ipynb        # Evaluation systems
├── building_moderation_filter.ipynb
├── generate_test_cases.ipynb   # Synthetic test data
├── how_to_enable_json_mode.ipynb
├── how_to_make_sql_queries.ipynb
├── metaprompt.ipynb            # Prompt engineering tool
├── pdf_upload_summarization.ipynb
├── prompt_caching.ipynb
├── read_web_pages_with_haiku.ipynb
├── sampling_past_max_tokens.ipynb
├── speculative_prompt_caching.ipynb
└── using_citations.ipynb

multimodal/                 # Vision and image processing
├── best_practices_for_vision.ipynb
├── crop_tool.ipynb             # Image region analysis
├── getting_started_with_vision.ipynb
├── how_to_transcribe_text.ipynb
├── reading_charts_graphs_powerpoints.ipynb
└── using_sub_agents.ipynb

observability/              # Monitoring and analytics
└── usage_cost_api.ipynb        # Admin API usage tracking

patterns/                   # Design patterns
└── agents/                 # Agent workflow patterns
    ├── basic_workflows.ipynb
    ├── evaluator_optimizer.ipynb
    └── orchestrator_workers.ipynb

scripts/                    # Validation and utility scripts
├── detect-secrets/         # Secret detection configuration
├── validate_all_notebooks.py
├── validate_authors_sorted.py
└── validate_notebooks.py

skills/                     # Claude Skills notebooks
├── notebooks/              # Skill tutorials
│   ├── 01_skills_introduction.ipynb
│   ├── 02_skills_financial_applications.ipynb
│   └── 03_skills_custom_development.ipynb
└── custom_skills/          # Example custom skills

third_party/                # Third-party integrations
├── Deepgram/               # Audio transcription
├── ElevenLabs/             # Voice assistant
├── LlamaIndex/             # RAG framework
├── MongoDB/                # Database RAG
├── Pinecone/               # Vector database
├── VoyageAI/               # Embeddings
├── Wikipedia/              # Knowledge retrieval
└── WolframAlpha/           # Computational queries

tool_evaluation/            # Tool evaluation frameworks
└── tool_evaluation.ipynb

tool_use/                   # Tool use and integration patterns
├── automatic-context-compaction.ipynb
├── calculator_tool.ipynb
├── customer_service_agent.ipynb
├── extracting_structured_json.ipynb
├── memory_cookbook.ipynb
├── parallel_tools.ipynb
├── programmatic_tool_calling_ptc.ipynb
├── tool_choice.ipynb
├── tool_search_with_embeddings.ipynb
├── tool_use_with_pydantic.ipynb
└── vision_with_tools.ipynb
```

## Registry System

Notebooks are tracked in two YAML files:

### registry.yaml

Central catalog of all cookbook notebooks with metadata:
```yaml
- title: Example Notebook Title
  description: Brief description of what this notebook teaches.
  path: category/notebook_name.ipynb
  authors:
  - github-username
  date: 'YYYY-MM-DD'
  categories:
  - Category Name
```

**Available categories:**
- Agent Patterns
- Claude Agent SDK
- Evals
- Fine-Tuning
- Integrations
- Multimodal
- Observability
- RAG & Retrieval
- Responses
- Skills
- Thinking
- Tools

### authors.yaml

Maps GitHub usernames to author details:
```yaml
github-username:
  name: Full Display Name
  website: https://github.com/github-username
  avatar: https://github.com/github-username.png
```

## Adding a New Cookbook

1. Create notebook in the appropriate directory
2. Run `/add-registry path/to/notebook.ipynb` or manually:
   - Add entry to `registry.yaml` with title, description, path, authors, categories, date
   - Add author info to `authors.yaml` if new contributor
3. Run quality checks: `make check`
4. Submit PR

## CI/CD Workflows

GitHub Actions automatically run:

| Workflow | Description |
|----------|-------------|
| `lint-format.yml` | Ruff linting and formatting checks |
| `notebook-quality.yml` | Notebook structure validation |
| `links.yml` | Link validation with lychee |
| `verify-authors.yml` | Authors.yaml validation |
| `claude-pr-review.yml` | Claude AI code review |
| `claude-model-check.yml` | Model name validation |
| `claude-link-review.yml` | Link quality review |
| `notebook-diff-comment.yml` | PR diff comments for notebooks |

## Cookbook Quality Standards

Good cookbooks follow these principles:

1. **Problem-first framing:** Lead with the problem being solved, not the machinery
2. **Learning objectives:** State what users will learn upfront
3. **Code presentation:** Explain before code blocks, describe insights after
4. **Use constants:** Define `MODEL` at the top of notebooks
5. **Clean setup:** Use `%%capture` for pip installs, `dotenv.load_dotenv()` for keys
6. **Actionable conclusions:** Map back to learning objectives, provide next steps

For detailed style guidelines, see `.claude/skills/cookbook-audit/style_guide.md`.

## Pre-commit Hooks

Automatically run before commits:
- `ruff-check`: Lint Python and Jupyter files
- `ruff-format`: Format code
- `validate-notebooks`: Check notebook structure
- `validate-authors-sorted`: Ensure authors.yaml is sorted

## Testing

```bash
# Validate notebook structure
uv run python scripts/validate_notebooks.py

# Run all pre-commit checks
uv run pre-commit run --all-files

# Test notebook execution (requires API key)
uv run jupyter nbconvert --to notebook \
  --execute path/to/notebook.ipynb \
  --ExecutePreprocessor.kernel_name=python3 \
  --output test_output.ipynb
```

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/anthropics/anthropic-cookbook/issues)
- **Discussions:** [GitHub Discussions](https://github.com/anthropics/anthropic-cookbook/discussions)
- **Discord:** [Anthropic Discord](https://www.anthropic.com/discord)
- **Documentation:** [docs.anthropic.com](https://docs.anthropic.com)
