# Ejentum <> Claude Cookbooks

[Ejentum](https://ejentum.com) is a Reasoning Harness for agentic AI: a library of 679 cognitive operations engineered in natural language, organized across four harnesses (`reasoning`, `code`, `anti-deception`, `memory`). Each harness call retrieves a task-matched scaffold rather than serving a fixed template: a named failure pattern, an executable procedure, suppression vectors that block the obvious shortcut, and an integrity check for self-verification. The model ingests the scaffold and writes from it.

* The [Anti-Deception Harness Notebook](./anti_deception_harness.ipynb) shows how to inject a sunk-cost-resistance scaffold into Claude's system prompt and observe the behavioral diff against an unaugmented baseline.

# More about Ejentum

- [Project repo](https://github.com/ejentum/ejentum-mcp) (MIT, includes the four `SKILL.md` files and editor adapters for Cursor, Windsurf, Cline)
- [Walkthrough with screenshots](https://ejentum.com/docs/claude_code_guide)
- ["Under Pressure" paper](https://doi.org/10.5281/zenodo.19392715) on the harness mechanism
- The same scaffolds are also available as MCP tools for Claude Code, Cursor, Cline, and Windsurf via `npx -y ejentum-mcp`

# Get Started

Free tier (100 calls, no card) at [ejentum.com/pricing](https://ejentum.com/pricing). Set the returned key as `EJENTUM_API_KEY` in your environment alongside your `ANTHROPIC_API_KEY`.
