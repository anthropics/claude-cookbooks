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
}


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

    if "Assistant" in msg.__class__.__name__:
        # Check if content exists and has elements
        if hasattr(msg, "content") and msg.content:
            first_block = msg.content[0]
            tool_name = first_block.name if hasattr(first_block, "name") else None

            if tool_name == "Task":
                # Extract subagent details from the Task tool input
                if hasattr(first_block, "input") and first_block.input:
                    subagent_type = first_block.input.get("subagent_type", "unknown")
                    description = first_block.input.get("description", "")
                    _subagent_context["active"] = True
                    _subagent_context["name"] = subagent_type
                    _subagent_context["depth"] += 1

                    print(f"🚀 Delegating to subagent: {subagent_type}")
                    if description:
                        print(f"   └─ Task: {description}")
                else:
                    print("🚀 Delegating to subagent...")
            elif tool_name:
                # Check if we're inside a subagent context
                if _subagent_context["active"]:
                    indent = "   " * _subagent_context["depth"]
                    print(f"{indent}📎 [{_subagent_context['name']}] Using: {tool_name}()")
                else:
                    print(f"🤖 Using: {tool_name}()")
            else:
                if _subagent_context["active"]:
                    indent = "   " * _subagent_context["depth"]
                    print(f"{indent}📎 [{_subagent_context['name']}] Thinking...")
                else:
                    print("🤖 Thinking...")
        else:
            if _subagent_context["active"]:
                indent = "   " * _subagent_context["depth"]
                print(f"{indent}📎 [{_subagent_context['name']}] Thinking...")
            else:
                print("🤖 Thinking...")

    elif "User" in msg.__class__.__name__:
        # Check if this is a Task tool result (subagent completed)
        if hasattr(msg, "content") and msg.content:
            for result in msg.content if isinstance(msg.content, list) else [msg.content]:
                if isinstance(result, dict) and result.get("type") == "tool_result":
                    # Try to detect if this was a Task result
                    content = result.get("content", "")
                    if isinstance(content, str) and (
                        "subagent" in content.lower() or _subagent_context["active"]
                    ):
                        if _subagent_context["active"]:
                            indent = "   " * _subagent_context["depth"]
                            print(f"{indent}✅ Subagent [{_subagent_context['name']}] completed")
                            _subagent_context["depth"] = max(0, _subagent_context["depth"] - 1)
                            if _subagent_context["depth"] == 0:
                                _subagent_context["active"] = False
                                _subagent_context["name"] = None
                        else:
                            print("✓ Task completed")
                        return

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
    in_subagent = False
    current_subagent: str | None = None
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

            for block in msg.content:
                if hasattr(block, "text"):
                    # Flush any pending tools before text
                    flush_pending_tools("   " if in_subagent else "")

                    text = block.text

                    if in_subagent:
                        print(f"\n   📎 [{current_subagent}] Response:")
                        # Indent the text nicely
                        for line in text.split("\n"):
                            if line.strip():
                                print(f"      {line.strip()}")
                    else:
                        print("\n🤖 Assistant:")
                        # Indent the text nicely
                        for line in text.split("\n"):
                            if line.strip():
                                print(f"   {line.strip()}")

                elif hasattr(block, "name"):
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}

                    if tool_name == "Task":
                        # Flush pending tools
                        flush_pending_tools("   " if in_subagent else "")

                        # Subagent delegation - create clear visual block
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
                        in_subagent = True
                        current_subagent = subagent_type

                    else:
                        # Regular tool - accumulate for grouped display
                        tool_info = _format_tool_info(tool_name, tool_input)
                        pending_tools.append(tool_info)

        elif msg_type == "UserMessage":
            if not msg.content or not isinstance(msg.content, list):
                continue

            for result in msg.content:
                if not isinstance(result, dict) or result.get("type") != "tool_result":
                    continue

                content = result.get("content", "")

                # Detect subagent completion (Task tool result with substantial content)
                is_subagent_result = in_subagent and isinstance(content, str) and len(content) > 200

                if is_subagent_result:
                    # Flush any pending tools
                    flush_pending_tools("   ")

                    # Show subagent completion
                    print()
                    print(f"   {SUBAGENT_TOP}")
                    print(_format_subagent_completion_line(current_subagent))
                    print(f"   {SUBAGENT_BOTTOM}")

                    # Show result summary
                    if content:
                        lines = [line.strip() for line in content.split("\n") if line.strip()]
                        if lines:
                            print("   📊 Result:")
                            for line in lines:
                                print(f"      {line}")
                    print()

                    in_subagent = False
                    current_subagent = None
                else:
                    # Regular tool result - just flush pending tools
                    # (tool results don't need individual display)
                    pass

            # Flush tools after processing user message
            flush_pending_tools("   " if in_subagent else "")

        elif msg_type == "ResultMessage":
            # Flush any remaining pending tools
            flush_pending_tools("   " if in_subagent else "")

            # Close subagent if still open
            if in_subagent:
                print()
                print(f"   {SUBAGENT_TOP}")
                print(_format_subagent_completion_line(current_subagent))
                print(f"   {SUBAGENT_BOTTOM}")
                in_subagent = False

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
