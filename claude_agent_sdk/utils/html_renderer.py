"""
HTML rendering utilities for Jupyter notebook display.

This module provides styled HTML card rendering for various content types,
designed for use in Jupyter notebooks with the Claude Agent SDK.

Content types supported:
- Images (file paths converted to base64)
- Pandas DataFrames and Series
- Agent message lists (extracts final assistant response)
- Generic Python objects (dicts, lists, strings)
"""

import base64
import html
import pprint
from typing import Any

# Optional dependencies with graceful fallback
HTML: Any = None
display: Any = None
pd: Any = None
markdown: Any = None

try:
    import pandas as pd
except ImportError:
    pass

try:
    from IPython.display import HTML, display
except ImportError:

    def display(obj: Any) -> None:
        """Fallback display for non-Jupyter environments."""
        print(obj.data if hasattr(obj, "data") else obj)

    class _HTML:
        """Fallback HTML wrapper for non-Jupyter environments."""

        def __init__(self, data: Any):
            self.data = data

    HTML = _HTML

try:
    import markdown as _markdown

    markdown = _markdown
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# CSS Constants
# ─────────────────────────────────────────────────────────────────────────────

CARD_CSS = """
<style>
.pretty-card {
    font-family: ui-sans-serif, system-ui;
    border: 2px solid transparent;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 10px 0;
    background: linear-gradient(#fff, #fff) padding-box,
                linear-gradient(135deg, #3b82f6, #9333ea) border-box;
    color: #111;
    box-shadow: 0 4px 12px rgba(0,0,0,.08);
}
.pretty-title {
    font-weight: 700;
    margin-bottom: 8px;
    font-size: 14px;
    color: #111;
}
.pretty-card pre,
.pretty-card code {
    background: #f3f4f6;
    color: #111;
    padding: 8px;
    border-radius: 8px;
    display: block;
    overflow-x: auto;
    font-size: 13px;
    white-space: pre-wrap;
}
.pretty-card img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
}
/* Tables: both pandas (.pretty-table) and markdown-rendered */
.pretty-card table {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    color: #111;
    margin: 0.5em 0;
}
.pretty-card th,
.pretty-card td {
    border: 1px solid #e5e7eb;
    padding: 6px 8px;
    text-align: left;
}
.pretty-card th {
    background: #f9fafb;
    font-weight: 600;
}
/* Markdown headings */
.pretty-card h1, .pretty-card h2, .pretty-card h3, .pretty-card h4 {
    margin: 0.5em 0 0.3em 0;
    color: #111;
}
.pretty-card h1 { font-size: 1.4em; }
.pretty-card h2 { font-size: 1.2em; }
.pretty-card h3 { font-size: 1.1em; }
/* Markdown lists and paragraphs */
.pretty-card ul, .pretty-card ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
}
.pretty-card p {
    margin: 0.5em 0;
}
.pretty-card hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1em 0;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Content Type Detection
# ─────────────────────────────────────────────────────────────────────────────


def _is_message_list(content: Any) -> bool:
    """
    Check if content is a list of SDK message objects.

    Uses duck-typing to check for message-like objects rather than
    relying on fragile class name string matching.
    """
    if not isinstance(content, list) or not content:
        return False

    # Check if any item looks like a message (has content attribute and message-like class)
    for item in content[-3:]:  # Check last few items for efficiency
        class_name = getattr(item, "__class__", type(None)).__name__
        if "Message" in class_name and hasattr(item, "content"):
            return True
    return False


def _is_dataframe(content: Any) -> bool:
    """Check if content is a pandas DataFrame."""
    return pd is not None and isinstance(content, pd.DataFrame)


def _is_series(content: Any) -> bool:
    """Check if content is a pandas Series."""
    return pd is not None and isinstance(content, pd.Series)


# ─────────────────────────────────────────────────────────────────────────────
# Content Renderers
# ─────────────────────────────────────────────────────────────────────────────


def _image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def _render_image(image_path: str) -> str:
    """
    Render an image path as an HTML img tag with base64 encoding.

    Args:
        image_path: Path to the image file

    Returns:
        HTML string with embedded base64 image
    """
    b64 = _image_to_base64(image_path)
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'alt="Image" style="max-width:100%; height:auto; border-radius:8px;">'
    )


def _render_dataframe(df: Any) -> str:
    """
    Render a pandas DataFrame as an HTML table.

    Args:
        df: pandas DataFrame

    Returns:
        HTML table string
    """
    result: str = df.to_html(classes="pretty-table", index=False, border=0, escape=True)
    return result


def _render_series(series: Any) -> str:
    """
    Render a pandas Series as an HTML table.

    Args:
        series: pandas Series

    Returns:
        HTML table string
    """
    result: str = series.to_frame().to_html(classes="pretty-table", border=0, escape=True)
    return result


def _render_message_list(messages: list[Any]) -> str:
    """
    Extract and render the final assistant text from a message list.

    Searches backwards through messages to find the last AssistantMessage
    with text content, then renders it (with markdown if available).

    Args:
        messages: List of SDK message objects

    Returns:
        Rendered HTML string
    """
    final_text = None

    for msg in reversed(messages):
        class_name = msg.__class__.__name__
        if "Assistant" in class_name and hasattr(msg, "content") and msg.content:
            for block in msg.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break
            if final_text:
                break

    if final_text:
        return _render_markdown_text(final_text)

    # Fallback: format the entire list
    return _render_code_block(pprint.pformat(messages))


def _render_markdown_text(text: str) -> str:
    """
    Render text as markdown HTML if the markdown library is available.

    Enables extensions for tables, fenced code blocks, and other common markdown features.

    Args:
        text: Plain text, potentially containing markdown

    Returns:
        HTML string
    """
    if markdown is not None:
        result: str = markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
        return result
    # Fallback: preserve whitespace and escape HTML
    return f"<pre style='white-space: pre-wrap;'>{html.escape(text)}</pre>"


def _render_code_block(content: str) -> str:
    """
    Render content as a code block.

    Args:
        content: String to display in code block

    Returns:
        HTML pre/code block string
    """
    return f"<pre><code>{html.escape(content)}</code></pre>"


def _render_generic(content: Any) -> str:
    """
    Render generic content (dicts, lists, strings, other objects).

    Args:
        content: Any Python object

    Returns:
        HTML string representation
    """
    if isinstance(content, (list, dict)):
        return _render_code_block(pprint.pformat(content))
    elif isinstance(content, str):
        return _render_code_block(content)
    else:
        return _render_code_block(str(content))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def render_content(content: Any, is_image: bool = False) -> str:
    """
    Detect content type and render to HTML.

    This is the main content routing function that dispatches to
    the appropriate renderer based on content type.

    Args:
        content: Content to render (image path, DataFrame, messages, etc.)
        is_image: If True, treat string content as an image path

    Returns:
        Rendered HTML string
    """
    # Image rendering (explicit flag)
    if is_image and isinstance(content, str):
        return _render_image(content)

    # Pandas DataFrame
    if _is_dataframe(content):
        return _render_dataframe(content)

    # Pandas Series
    if _is_series(content):
        return _render_series(content)

    # SDK message list
    if _is_message_list(content):
        return _render_message_list(content)

    # Generic fallback
    return _render_generic(content)


def display_card(content: str, title: str | None = None) -> None:
    """
    Display rendered HTML content inside a styled card.

    Args:
        content: Pre-rendered HTML content
        title: Optional title for the card
    """
    title_html = f'<div class="pretty-title">{html.escape(title)}</div>' if title else ""
    card_html = f'<div class="pretty-card">{title_html}{content}</div>'
    display(HTML(CARD_CSS + card_html))


def display_agent_response(messages: list[Any], title: str = "Agent Response") -> None:
    """
    Display the final assistant response from a conversation in a styled card.

    Extracts the last text response from an agent's message history and
    renders it with markdown formatting in a visually appealing card.

    Args:
        messages: List of SDK message objects from agent conversation
        title: Card title (default: "Agent Response")

    Example:
        >>> async for msg in query(prompt="Research AI trends", ...):
        ...     messages.append(msg)
        >>> display_agent_response(messages)
    """
    if not _is_message_list(messages):
        raise TypeError(
            "Expected a list of SDK message objects. "
            "Use display_card() or render_content() for other content types."
        )
    rendered = _render_message_list(messages)
    display_card(rendered, title)


# ─────────────────────────────────────────────────────────────────────────────
# Conversation Timeline (HTML)
# ─────────────────────────────────────────────────────────────────────────────

TIMELINE_CSS = """
<style>
.conversation-timeline {
    font-family: ui-sans-serif, system-ui;
    max-width: 900px;
    margin: 1em 0;
}
.timeline-header {
    background: linear-gradient(135deg, #3b82f6, #9333ea);
    color: white;
    padding: 12px 16px;
    border-radius: 12px 12px 0 0;
    font-weight: 700;
    font-size: 14px;
}
.timeline-body {
    border: 1px solid #e5e7eb;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 12px;
    background: #fafafa;
}
.msg-block {
    margin: 8px 0;
    padding: 10px 12px;
    border-radius: 8px;
    background: white;
    border-left: 3px solid #e5e7eb;
}
.msg-block.system { border-left-color: #6b7280; }
.msg-block.assistant { border-left-color: #3b82f6; }
.msg-block.tool { border-left-color: #10b981; background: #f0fdf4; }
.msg-block.subagent { border-left-color: #9333ea; background: #faf5ff; }
.msg-block.result { border-left-color: #f59e0b; background: #fffbeb; }
.msg-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 4px;
}
.msg-content {
    font-size: 13px;
    color: #111;
}
.msg-content pre {
    background: #f3f4f6;
    padding: 8px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 12px;
}
.tool-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 4px;
}
.tool-badge {
    background: #e0f2fe;
    color: #0369a1;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-family: monospace;
}
.stats-bar {
    display: flex;
    gap: 16px;
    padding: 10px 12px;
    background: #f9fafb;
    border-radius: 8px;
    font-size: 12px;
    color: #374151;
    margin-top: 8px;
}
.stat-item { display: flex; gap: 4px; }
.stat-label { color: #6b7280; }
</style>
"""


def _extract_model_from_messages(messages: list[Any]) -> str | None:
    """Extract model identifier from messages."""
    for msg in messages:
        msg_type = msg.__class__.__name__
        if msg_type == "SystemMessage":
            if hasattr(msg, "data") and isinstance(msg.data, dict):
                if "model" in msg.data:
                    return str(msg.data["model"])
        if msg_type == "ResultMessage":
            if hasattr(msg, "model"):
                return str(msg.model)
    return None


def _format_tool_badge(tool_name: str, tool_input: dict | None = None) -> str:
    """Format a tool call as an HTML badge."""
    info = tool_name
    if tool_input:
        if tool_name == "WebSearch" and "query" in tool_input:
            info = f'{tool_name}: "{tool_input["query"][:30]}..."'
        elif tool_name == "Read" and "file_path" in tool_input:
            filename = tool_input["file_path"].split("/")[-1]
            info = f"{tool_name}: {filename}"
    return f'<span class="tool-badge">{html.escape(info)}</span>'


def visualize_conversation_html(messages: list[Any]) -> None:
    """
    Render the full conversation as a styled HTML timeline.

    Displays system init, tool calls, assistant responses, and subagent delegations
    in a visually appealing format for Jupyter notebooks.

    Args:
        messages: List of SDK message objects
    """
    if not messages:
        return

    model = _extract_model_from_messages(messages)
    blocks: list[str] = []
    pending_tools: list[str] = []

    def flush_tools() -> None:
        nonlocal pending_tools
        if pending_tools:
            tools_html = "".join(pending_tools)
            blocks.append(
                f'<div class="msg-block tool">'
                f'<div class="msg-label">🔧 Tools</div>'
                f'<div class="tool-list">{tools_html}</div>'
                f"</div>"
            )
            pending_tools = []

    for msg in messages:
        msg_type = msg.__class__.__name__

        if msg_type == "SystemMessage":
            session_id = ""
            if hasattr(msg, "data") and isinstance(msg.data, dict):
                if "session_id" in msg.data:
                    session_id = f" ({msg.data['session_id'][:8]}...)"
            blocks.append(
                f'<div class="msg-block system">'
                f'<div class="msg-label">⚙️ System</div>'
                f'<div class="msg-content">Initialized{session_id}</div>'
                f"</div>"
            )

        elif msg_type == "AssistantMessage":
            if not msg.content:
                continue

            for block in msg.content:
                if hasattr(block, "text"):
                    flush_tools()
                    text_html = _render_markdown_text(block.text)
                    blocks.append(
                        f'<div class="msg-block assistant">'
                        f'<div class="msg-label">🤖 Assistant</div>'
                        f'<div class="msg-content">{text_html}</div>'
                        f"</div>"
                    )
                elif hasattr(block, "name"):
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}

                    if tool_name == "Task":
                        flush_tools()
                        subagent_type = (
                            tool_input.get("subagent_type", "unknown") if tool_input else "unknown"
                        )
                        description = tool_input.get("description", "") if tool_input else ""
                        blocks.append(
                            f'<div class="msg-block subagent">'
                            f'<div class="msg-label">🚀 Subagent: {html.escape(subagent_type)}</div>'
                            f'<div class="msg-content">{html.escape(description)}</div>'
                            f"</div>"
                        )
                    else:
                        pending_tools.append(_format_tool_badge(tool_name, tool_input))

        elif msg_type == "ResultMessage":
            flush_tools()

            # Build stats
            stats_html = ""
            stats = []
            if hasattr(msg, "num_turns") and msg.num_turns:
                stats.append(
                    f'<span class="stat-item"><span class="stat-label">Turns:</span> {msg.num_turns}</span>'
                )
            if hasattr(msg, "usage") and msg.usage:
                total = msg.usage.get("input_tokens", 0) + msg.usage.get("output_tokens", 0)
                stats.append(
                    f'<span class="stat-item"><span class="stat-label">Tokens:</span> {total:,}</span>'
                )
            if hasattr(msg, "total_cost_usd") and msg.total_cost_usd:
                stats.append(
                    f'<span class="stat-item"><span class="stat-label">Cost:</span> ${msg.total_cost_usd:.2f}</span>'
                )
            if hasattr(msg, "duration_ms") and msg.duration_ms:
                stats.append(
                    f'<span class="stat-item"><span class="stat-label">Duration:</span> {msg.duration_ms / 1000:.1f}s</span>'
                )

            if stats:
                stats_html = f'<div class="stats-bar">{" ".join(stats)}</div>'

            blocks.append(
                f'<div class="msg-block result">'
                f'<div class="msg-label">✅ Complete</div>'
                f"{stats_html}"
                f"</div>"
            )

    # Assemble timeline
    model_text = f" • {model}" if model else ""
    timeline_html = f"""
    {TIMELINE_CSS}
    <div class="conversation-timeline">
        <div class="timeline-header">🤖 Agent Conversation Timeline{model_text}</div>
        <div class="timeline-body">
            {"".join(blocks)}
        </div>
    </div>
    """
    display(HTML(timeline_html))
