# GetXAPI <> Claude Cookbooks

[GetXAPI](https://www.getxapi.com) provides a REST API for the Twitter / X platform — search tweets, look up users, read replies and followers, and post tweets, send DMs, and manage articles. Authentication is a single bearer token.

This cookbook shows how to give Claude tool access to GetXAPI so the model can answer real-time questions about Twitter / X (recent tweets, user profiles, follower graph, replies) inside a single tool-use loop.

## What's Included

* **[Twitter Research Agent Notebook](./twitter_research_agent.ipynb)** — Builds a Claude agent that researches a topic on Twitter / X using the GetXAPI tweet-search and user-info endpoints. Demonstrates tool definitions, a tool-use loop, and how to render the final synthesis.

## How to Use This Cookbook

### Step 1: Set Up Your Environment

1. **Create a virtual environment:**

   ```bash
   cd /path/to/claude-cookbooks/third_party/GetXAPI

   python -m venv venv
   source venv/bin/activate    # macOS / Linux
   # OR
   venv\Scripts\activate       # Windows
   ```

2. **Get your API keys:**

   - **GetXAPI key:** sign up at [getxapi.com](https://www.getxapi.com) and copy the key from the dashboard. Read endpoints (search, user info, followers, replies, mentions, timeline) need this key only.
   - **Anthropic API key:** [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

3. **Configure your environment:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add both keys:

   ```
   GETXAPI_KEY=get-x-api-...
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Run the Notebook

Open `twitter_research_agent.ipynb` in Jupyter (or VS Code) and run the cells top-to-bottom. The notebook walks through:

- Defining two Claude tools (`search_tweets`, `get_user_info`) that wrap GetXAPI endpoints
- The tool-use loop pattern — Claude requests a tool, the notebook executes it, the result is returned, and Claude either calls another tool or produces the final answer
- How to surface tool inputs and outputs so you can audit what the agent did

The example task is open-ended: *"Find recent tweets about Claude agents and summarize what people are building."* You can swap the task with anything that benefits from live Twitter / X data — tracking competitor launches, finding domain experts on a topic, surfacing community sentiment about a release.

## API Surface Used in This Cookbook

The notebook calls two of GetXAPI's 47 endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /twitter/tweet/advanced_search` | Search tweets by query string |
| `GET /twitter/user/info` | Look up a user profile by username |

The full OpenAPI 3.1 spec covers tweets (search, detail, replies, create, like, retweet, bookmark, delete), users (search, info, followers, following, verified followers, media, tweets, mentions, timeline), articles, DMs, lists, and media upload — see [docs.getxapi.com](https://docs.getxapi.com).

Authentication is `Authorization: Bearer <GETXAPI_KEY>` on every request.

## Troubleshooting

### `401 Unauthorized`

Verify `GETXAPI_KEY` is set correctly and the dashboard shows an active key. The bearer header must be exactly `Authorization: Bearer <key>` (no `Token` prefix, no extra spaces).

### `429 Too Many Requests`

You've hit a rate limit. Wait a minute and retry, or check your usage in the dashboard.

### Empty `tweets` array on a query you expect results for

Some queries return no results when the `product` parameter defaults to `Top` (Twitter's relevance filter). Pass `product=Latest` for chronological results or `product=People` for user matches.

### Anthropic SDK version

This notebook uses the `messages.create` tool-use loop. If you see `AttributeError`, upgrade the SDK:

```bash
pip install --upgrade anthropic
```

## Extending This Cookbook

Some natural extensions of this pattern:

- **Topic monitor** — schedule the agent to run hourly, summarizing new tweets on a topic into a digest
- **Reply researcher** — feed a tweet URL, walk the reply tree, and surface the highest-signal responses
- **Account auditor** — given a username, pull recent tweets, followers, and engagement and ask Claude to describe the account's positioning
- **Launch tracker** — search for tweets mentioning a product launch and cluster them by sentiment

For write tools (post tweets, send DMs, publish articles), the GetXAPI server accepts the same bearer auth plus an X account session token — see the [docs](https://docs.getxapi.com) for the write-tool auth flow.

## More About GetXAPI

- [Website](https://www.getxapi.com)
- [API documentation](https://docs.getxapi.com)
- [OpenAPI 3.1 spec](https://docs.getxapi.com/openapi.json)
- [MCP server](https://github.com/getxapi/getxapi-mcp) — the same API exposed as an MCP server for Claude Desktop, Cursor, and other MCP clients
- [Code samples](https://github.com/getxapi/getxapi-examples) — curl, Python, Node.js, Go
