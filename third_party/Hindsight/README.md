# Hindsight <> Claude Agent SDK

[Hindsight](https://github.com/vectorize-io/hindsight) is an open-source (MIT) long-term memory engine for AI agents. The [`hindsight-claude-agent-sdk`](https://pypi.org/project/hindsight-claude-agent-sdk/) package gives a Claude Agent SDK agent memory that persists across sessions — via in-process MCP tools (`retain` / `recall` / `reflect`) and automatic memory hooks.

Here we provide a cookbook for adding persistent memory to Claude Agent SDK agents with Hindsight.

1. `claude_agent_sdk_memory.ipynb` - Build a Claude agent that remembers user preferences, decisions, and project context across sessions, using both explicit memory tools and automatic recall/retain hooks.

[Hindsight GitHub](https://github.com/vectorize-io/hindsight)
[Documentation](https://docs.hindsight.vectorize.io)
[PyPI](https://pypi.org/project/hindsight-claude-agent-sdk/)
