"""
Visualization utilities for Claude Agent SDK conversations.

This module is the PUBLIC API for all display functions in notebooks:
- Real-time activity tracking (print_activity)
- Conversation timelines (visualize_conversation)
- Final result display (print_final_result)
- Styled HTML card display (display_agent_response)

Example usage::

    from utils.agent_visualizer import (
        print_activity,
        reset_activity_context,
        visualize_conversation,
        display_agent_response,
    )

    # Track activity during agent execution
    reset_activity_context()
    messages = []
    async for msg in agent.receive_response():
        print_activity(msg)
        messages.append(msg)

    # Display results (auto-detects Jupyter vs terminal)
    visualize_conversation(messages)
    display_agent_response(messages)
"""

from typing import Any

from utils.html_renderer import display_agent_response, visualize_conversation_html

__all__ = [
    "display_agent_response",
    "print_activity",
    "print_final_result",
    "reset_activity_context",
    "visualize_conversation",
]


def _is_jupyter() -> bool:
    """
    Detect if running in a Jupyter notebook environment.

    Returns True for Jupyter notebook/lab, False for terminal/scripts.
    """
    try:
        from IPython import get_ipython

        shell = get_ipython()
        if shell is None:
            return False
        return bool(shell.__class__.__name__ == "ZMQInteractiveShell")
    except ImportError:
        return False
    except Exception:
        return False


# Box-drawing configuration constants
BOX_WIDTH = 58  # Width for main conversation boxes
SUBAGENT_WIDTH = 54  # Width for subagent delegation blocks (slightly narrower for visual hierarchy)

# Box-drawing characters for clean visual formatting
BOX_TOP = "╭" + "─" * BOX_WIDTH + "╮"
BOX_BOTTOM = "╰" + "─" * BOX_WIDTH + "╯"
BOX_DIVIDER = "├" + "─" * BOX_WIDTH + "┤"
BOX_SIDE = "│"
SUBAGENT_TOP = "┌" + "─" * SUBAGENT_WIDTH + "┐"
SUBAGENT_BOTTOM = "└" + "─" * SUBAGENT_WIDTH + "┘"
SUBAGENT_SIDE = "│"


def extract_model_from_messages(messages: list[Any]) -> str | None:
    """
    Extract the model identifier from a list of messages.

    Looks for model information in SystemMessage or ResultMessage.

    Args:
        messages: List of conversation messages

    Returns:
        Model identifier string or None if not found
    """
    for msg in messages:
        msg_type = msg.__class__.__name__

        # Check SystemMessage for model info
        if msg_type == "SystemMessage":
            if hasattr(msg, "data") and isinstance(msg.data, dict):
                if "model" in msg.data:
                    return str(msg.data["model"])

        # Check ResultMessage for model info
        if msg_type == "ResultMessage":
            if hasattr(msg, "model"):
                return str(msg.model)

    return None


# Track subagent state for activity display
# WARNING: This global state is NOT thread-safe. If using this module in concurrent
# scenarios (e.g., multiple asyncio tasks processing different conversations simultaneously),
# each task should call reset_activity_context() before starting and be aware that
# interleaved operations may produce incorrect subagent tracking. For thread-safe usage,
# consider passing context explicitly or using contextvars.
_subagent_context: dict[str, Any] = {
    "active": False,
    "name": None,
    "depth": 0,
    "stack": [],
}


def _extract_tool_result(block: Any) -> tuple[str | None, str] | None:
    if isinstance(block, dict):
        if block.get("type") != "tool_result":
            return None
        raw_content = block.get("content", "")
        tool_use_id = block.get("tool_use_id")
    elif hasattr(block, "tool_use_id") or block.__class__.__name__ == "ToolResultBlock":
        raw_content = getattr(block, "content", "")
        tool_use_id = getattr(block, "tool_use_id", None)
    else:
        return None

    if isinstance(raw_content, str):
        text = raw_content
    elif isinstance(raw_content, list):
        parts = []
        for item in raw_content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        text = "\n".join(parts)
    else:
        text = ""
    return (str(tool_use_id) if tool_use_id else None), text


def _active_subagent_name(stack: list[tuple[str | None, str]], msg: Any) -> str | None:
    parent_id = getattr(msg, "parent_tool_use_id", None)
    if parent_id:
        for tid, name in reversed(stack):
            if tid == parent_id:
                return name
    return stack[-1][1] if stack else None


def _pop_completed_subagent(
    stack: list[tuple[str | None, str]],
    tool_use_id: str | None,
    content: str,
) -> str | None:
    if tool_use_id is not None:
        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == tool_use_id:
                return stack.pop(i)[1]
        return None
    for i in range(len(stack) - 1, -1, -1):
        if stack[i][0] is None and ("subagent" in content.lower() or len(content) > 200):
            return stack.pop(i)[1]
    return None


def _sync_subagent_context() -> None:
    stack = _subagent_context["stack"]
    _subagent_context["depth"] = len(stack)
    _subagent_context["active"] = bool(stack)
    _subagent_context["name"] = stack[-1][1] if stack else None


def print_activity(msg: Any) -> None:
    """
    Print activity with enhanced subagent visibility.

    Shows:
    - Main agent tool usage with 🤖
    - Subagent invocations with 🚀 and subagent name
    - Subagent tool usage with indented 📎

    Example::

        async for msg in agent.receive_response():
            print_activity(msg)  # Prints: 🤖 Using: WebSearch()
            messages.append(msg)

    Args:
        msg: A message object from the Claude Agent SDK response stream
    """
    global _subagent_context
    stack: list[tuple[str | None, str]] = _subagent_context.setdefault("stack", [])

    if "Assistant" in msg.__class__.__name__:
        blocks = msg.content if hasattr(msg, "content") and msg.content else []
        tool_blocks = [b for b in blocks if getattr(b, "name", None)]
        if tool_blocks:
            for block in tool_blocks:
                tool_name = block.name
                if tool_name in ("Agent", "Task"):
                    tool_input = getattr(block, "input", None)
                    tool_id = getattr(block, "id", None)
                    if isinstance(tool_input, dict) and tool_input:
                        subagent_type = tool_input.get("subagent_type", "unknown")
                        description = tool_input.get("description", "")
                        stack.append((tool_id, subagent_type))
                        _sync_subagent_context()

                        print(f"🚀 Delegating to subagent: {subagent_type}")
                        if description:
                            print(f"   └─ Task: {description}")
                    else:
                        if tool_id is not None:
                            stack.append((tool_id, "unknown"))
                            _sync_subagent_context()
                        print("🚀 Delegating to subagent...")
                elif _subagent_context["active"]:
                    active_name = _active_subagent_name(stack, msg) or _subagent_context["name"]
                    indent = "   " * _subagent_context["depth"]
                    print(f"{indent}📎 [{active_name}] Using: {tool_name}()")
                else:
                    print(f"🤖 Using: {tool_name}()")
        elif _subagent_context["active"]:
            active_name = _active_subagent_name(stack, msg) or _subagent_context["name"]
            indent = "   " * _subagent_context["depth"]
            print(f"{indent}📎 [{active_name}] Thinking...")
        else:
            print("🤖 Thinking...")

    elif "User" in msg.__class__.__name__:
        handled = False
        if hasattr(msg, "content") and msg.content:
            raw_items = msg.content if isinstance(msg.content, list) else [msg.content]
            for item in raw_items:
                parsed = _extract_tool_result(item)
                if parsed is None:
                    continue
                tool_use_id, content = parsed
                depth_before = _subagent_context["depth"]
                completed_name = _pop_completed_subagent(stack, tool_use_id, content)
                if completed_name is not None:
                    _sync_subagent_context()
                    indent = "   " * max(1, depth_before)
                    print(f"{indent}✅ Subagent [{completed_name}] completed")
                    handled = True
                elif not _subagent_context["active"] and "subagent" in content.lower():
                    print("✓ Task completed")
                    handled = True
                else:
                    indent = (
                        "   " * _subagent_context["depth"] if _subagent_context["active"] else ""
                    )
                    print(f"{indent}✓ Tool completed")
                    handled = True

        if not handled:
            if _subagent_context["active"]:
                indent = "   " * _subagent_context["depth"]
                print(f"{indent}✓ Tool completed")
            else:
                print("✓ Tool completed")


def reset_activity_context() -> None:
    """
    Reset the subagent tracking context.

    Call before starting a new query to ensure clean state for subagent tracking.

    Example::

        # Before each new query
        reset_activity_context()
        await agent.query("New research question")
        async for msg in agent.receive_response():
            print_activity(msg)
    """
    global _subagent_context
    _subagent_context = {
        "active": False,
        "name": None,
        "depth": 0,
        "stack": [],
    }


def print_final_result(messages: list[Any], model: str | None = None) -> None:
    """
    Print the final agent result and cost information.

    Args:
        messages: List of conversation messages
        model: Optional model identifier for cost calculation.
               If not provided, will attempt to extract from messages.
    """
    if not messages:
        return

    # Get the result message (last message)
    result_msg = messages[-1]

    # Try to extract model from messages if not provided
    if model is None:
        model = extract_model_from_messages(messages)

    # Find the last assistant message with actual content
    for msg in reversed(messages):
        if msg.__class__.__name__ == "AssistantMessage" and msg.content:
            # Check if it has text content (not just tool use)
            for block in msg.content:
                if hasattr(block, "text"):
                    print(f"\n📝 Final Result:\n{block.text}")
                    break
            break

    # Print cost (use reported cost from SDK - it's authoritative)
    # Note: total_cost_usd is model-aware and calculated by the API
    reported_cost = getattr(result_msg, "total_cost_usd", None)
    num_turns = getattr(result_msg, "num_turns", 1)

    if reported_cost is not None:
        print(f"\n📊 Cost: ${reported_cost:.2f}")
        if num_turns and num_turns > 1:
            avg_cost = reported_cost / num_turns
            print(f"   ({num_turns} turns, avg ${avg_cost:.4f}/turn)")

    # Show model info
    if model:
        print(f"   Model: {model}")

    # Print duration if available
    if hasattr(result_msg, "duration_ms"):
        print(f"⏱️  Duration: {result_msg.duration_ms / 1000:.2f}s")


def _format_tool_info(tool_name: str, tool_input: dict) -> str:
    """Format tool information with relevant parameters."""
    info_parts = [tool_name]

    if tool_input:
        if tool_name == "WebSearch" and "query" in tool_input:
            info_parts.append(f'→ "{tool_input["query"]}"')
        elif tool_name == "Bash" and "command" in tool_input:
            cmd = tool_input["command"]
            info_parts.append(f"→ {cmd}")
        elif tool_name == "Read" and "file_path" in tool_input:
            path = tool_input["file_path"]
            # Show just filename for readability
            filename = path.split("/")[-1] if "/" in path else path
            info_parts.append(f"→ {filename}")
        elif tool_name == "Write" and "file_path" in tool_input:
            path = tool_input["file_path"]
            filename = path.split("/")[-1] if "/" in path else path
            info_parts.append(f"→ {filename}")

    return " ".join(info_parts)


def _format_subagent_completion_line(subagent_name: str | None) -> str:
    """
    Format a subagent completion line with safe handling of None and long names.

    Args:
        subagent_name: Name of the subagent (may be None)

    Returns:
        Formatted completion line string
    """
    name = (subagent_name or "unknown").upper()
    # Calculate padding, ensuring it's never negative
    padding = max(0, 30 - len(name))
    return f"   {SUBAGENT_SIDE}  ✅ SUBAGENT [{name}] COMPLETE" + " " * padding + SUBAGENT_SIDE


def visualize_conversation(messages: list[Any]) -> None:
    """
    Create a clean, professional visualization of the agent conversation.

    Auto-detects environment:
    - Jupyter notebooks: Renders styled HTML timeline with color-coded message blocks
    - Terminal/scripts: Falls back to box-drawing character visualization

    Features (both modes):
    - Grouped tool calls
    - Clear subagent delegation sections
    - Model-aware cost breakdown

    Example::

        messages = []
        async for msg in agent.receive_response():
            messages.append(msg)

        # Renders HTML in Jupyter, box-drawing in terminal
        visualize_conversation(messages)

    Args:
        messages: List of message objects from the agent response
    """
    # Auto-detect: use HTML in Jupyter, terminal fallback elsewhere
    if _is_jupyter():
        visualize_conversation_html(messages)
        return

    # Terminal fallback: box-drawing visualization
    # Extract model info for cost calculations
    model = extract_model_from_messages(messages)

    # Header
    print()
    print(BOX_TOP)
    print(f"{BOX_SIDE}  🤖 AGENT CONVERSATION TIMELINE" + " " * 25 + BOX_SIDE)
    print(BOX_BOTTOM)
    print()
    print(f"📝 Model: {model or 'unknown'}")

    # Track state
    active_subagents: list[tuple[str | None, str]] = []
    pending_tools: list[str] = []  # Collect consecutive tool calls

    def flush_pending_tools(indent: str = "") -> None:
        """Print accumulated tool calls in a compact format."""
        nonlocal pending_tools
        if pending_tools:
            if len(pending_tools) == 1:
                print(f"{indent}   🔧 {pending_tools[0]}")
            else:
                print(f"{indent}   🔧 Tools: {', '.join(pending_tools)}")
            pending_tools = []

    for msg in messages:
        msg_type = msg.__class__.__name__

        if msg_type == "SystemMessage":
            session_id = ""
            if hasattr(msg, "data") and "session_id" in msg.data:
                session_id = f" (Session: {msg.data['session_id'][:8]}...)"
            print(f"⚙️  System Initialized{session_id}")

        elif msg_type == "AssistantMessage":
            if not msg.content:
                continue

            active_name = _active_subagent_name(active_subagents, msg)

            for block in msg.content:
                if hasattr(block, "text"):
                    flush_pending_tools("   " if active_name else "")

                    text = block.text

                    if active_name:
                        print(f"\n   📎 [{active_name}] Response:")
                        for line in text.split("\n"):
                            if line.strip():
                                print(f"      {line.strip()}")
                    else:
                        print("\n🤖 Assistant:")
                        for line in text.split("\n"):
                            if line.strip():
                                print(f"   {line.strip()}")

                elif hasattr(block, "name"):
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}

                    if tool_name in ("Agent", "Task"):  # subagent tool ("Task" before SDK 0.2)
                        flush_pending_tools("   " if active_name else "")

                        subagent_type = (
                            tool_input.get("subagent_type", "unknown") if tool_input else "unknown"
                        )
                        description = tool_input.get("description", "") if tool_input else ""
                        prompt = tool_input.get("prompt", "") if tool_input else ""

                        print()
                        print(f"   {SUBAGENT_TOP}")
                        print(
                            f"   {SUBAGENT_SIDE}  🚀 DELEGATING TO: {subagent_type.upper():<36} {SUBAGENT_SIDE}"
                        )
                        if description:
                            print(f"   {SUBAGENT_SIDE}     📋 {description:<45} {SUBAGENT_SIDE}")
                        print(f"   {SUBAGENT_BOTTOM}")

                        if prompt:
                            print(f"   📝 Prompt: {prompt}")

                        print()
                        active_subagents.append((getattr(block, "id", None), subagent_type))
                        active_name = subagent_type

                    else:
                        tool_info = _format_tool_info(tool_name, tool_input)
                        pending_tools.append(tool_info)

        elif msg_type == "UserMessage":
            if not msg.content:
                continue

            raw_items = msg.content if isinstance(msg.content, list) else [msg.content]
            for result in raw_items:
                parsed = _extract_tool_result(result)
                if parsed is None:
                    continue

                tool_use_id, content = parsed
                completed_subagent = _pop_completed_subagent(active_subagents, tool_use_id, content)

                if completed_subagent is not None:
                    flush_pending_tools("   ")

                    print()
                    print(f"   {SUBAGENT_TOP}")
                    print(_format_subagent_completion_line(completed_subagent))
                    print(f"   {SUBAGENT_BOTTOM}")

                    if content:
                        lines = [line.strip() for line in content.split("\n") if line.strip()]
                        if lines:
                            print("   📊 Result:")
                            for line in lines:
                                print(f"      {line}")
                    print()

            flush_pending_tools("   " if active_subagents else "")

        elif msg_type == "ResultMessage":
            flush_pending_tools("   " if active_subagents else "")

            while active_subagents:
                _, remaining_subagent = active_subagents.pop()
                print()
                print(f"   {SUBAGENT_TOP}")
                print(_format_subagent_completion_line(remaining_subagent))
                print(f"   {SUBAGENT_BOTTOM}")

            # Final stats
            print()
            print("─" * 60)
            stats_parts = []
            num_turns = getattr(msg, "num_turns", 1)
            if num_turns:
                stats_parts.append(f"Turns: {num_turns}")

            # Extract token usage (note: this is cumulative across all turns)
            input_tokens = 0
            output_tokens = 0
            if hasattr(msg, "usage") and msg.usage:
                input_tokens = msg.usage.get("input_tokens", 0)
                output_tokens = msg.usage.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                stats_parts.append(f"Tokens: {total_tokens:,}")

            # Show cost (use reported cost from SDK - it's authoritative)
            reported_cost = getattr(msg, "total_cost_usd", None)
            if reported_cost:
                stats_parts.append(f"Cost: ${reported_cost:.2f}")

            if hasattr(msg, "duration_ms"):
                stats_parts.append(f"Duration: {msg.duration_ms / 1000:.1f}s")

            print(f"✅ Complete │ {' │ '.join(stats_parts)}")

            # Show model info
            if model:
                print(f"📊 Model: {model}")

            print("─" * 60)

    print()
