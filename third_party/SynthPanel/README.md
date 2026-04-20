# SynthPanel <> Claude Cookbooks

[SynthPanel](https://github.com/DataViking-Tech/SynthPanel) is an open-source (MIT) research harness that runs synthetic focus groups using AI personas. It ships a 12-tool [Model Context Protocol](https://modelcontextprotocol.io) server so Claude Code, Cursor, Windsurf, Zed, or any MCP-capable agent can drive a panel end-to-end from a natural-language prompt.

This cookbook walks through both surfaces:

1. `Synthetic_Focus_Group_With_SynthPanel.ipynb` — Register the SynthPanel MCP server with Claude Code, then run a synthetic focus group two ways: (a) by asking Claude Code to call the MCP tools in natural language, and (b) by using the Python SDK directly so you can see exactly what those tools call under the hood. Covers single prompts, a three-persona quick poll, and a v3 branching instrument where the moderator logic picks its own probe path based on the themes that surface.

## Links

- Repo: <https://github.com/DataViking-Tech/SynthPanel>
- Docs: <https://synthpanel.dev>
- MCP spec: <https://modelcontextprotocol.io>
- PyPI: `pip install 'synthpanel[mcp]'`
- License: MIT
