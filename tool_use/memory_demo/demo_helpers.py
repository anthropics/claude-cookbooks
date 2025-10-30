"""
Helper functions for memory cookbook demos.

This module provides reusable functions for running conversation loops
with Claude, handling tool execution, and managing context.
"""

from typing import Any

from anthropic import Anthropic
from memory_tool import MemoryToolHandler


def execute_tool(tool_use: Any, memory_handler: MemoryToolHandler) -> str:
    """
    Execute a tool use and return the result.

    Args:
        tool_use: The tool use object from Claude's response
        memory_handler: The memory tool handler instance

    Returns:
        str: The result of the tool execution
    """
    if tool_use.name == "memory":
        result = memory_handler.execute(**tool_use.input)
        return result.get("success") or result.get("error", "Unknown error")
    return f"Unknown tool: {tool_use.name}"


def run_conversation_turn(
    client: Anthropic,
    model: str,
    messages: list[dict[str, Any]],
    memory_handler: MemoryToolHandler,
    system: str,
    context_management: dict[str, Any] | None = None,
    max_tokens: int = 1024,
    verbose: bool = False,
) -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run a single conversation turn, handling tool uses.

    Args:
        client: Anthropic client instance
        model: Model to use
        messages: Current conversation messages
        memory_handler: Memory tool handler instance
        system: System prompt
        context_management: Optional context management config
        max_tokens: Max tokens for response
        verbose: Whether to print tool operations

    Returns:
        Tuple of (response, assistant_content, tool_results)
    """
    memory_tool: dict[str, Any] = {"type": "memory_20250818", "name": "memory"}

    request_params: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
        "tools": [memory_tool],
        "betas": ["context-management-2025-06-27"],
    }

    if context_management:
        request_params["context_management"] = context_management

    response = client.beta.messages.create(**request_params)

    assistant_content = []
    tool_results = []

    for content in response.content:
        if content.type == "text":
            if verbose:
                print(f"💬 Claude: {content.text}\n")
            assistant_content.append({"type": "text", "text": content.text})
        elif content.type == "tool_use":
            if verbose:
                cmd = content.input.get("command")
                path = content.input.get("path", "")
                print(f"  🔧 Memory tool: {cmd} {path}")

            result = execute_tool(content, memory_handler)

            if verbose:
                result_preview = result[:80] + "..." if len(result) > 80 else result
                print(f"  ✓ Result: {result_preview}")

            assistant_content.append(
                {"type": "tool_use", "id": content.id, "name": content.name, "input": content.input}
            )
            tool_results.append(
                {"type": "tool_result", "tool_use_id": content.id, "content": result}
            )

    return response, assistant_content, tool_results


def run_conversation_loop(
    client: Anthropic,
    model: str,
    messages: list[dict[str, Any]],
    memory_handler: MemoryToolHandler,
    system: str,
    context_management: dict[str, Any] | None = None,
    max_tokens: int = 1024,
    max_turns: int = 5,
    verbose: bool = False,
) -> Any:
    """
    Run a complete conversation loop until Claude stops using tools.

    Args:
        client: Anthropic client instance
        model: Model to use
        messages: Current conversation messages (will be modified in-place)
        memory_handler: Memory tool handler instance
        system: System prompt
        context_management: Optional context management config
        max_tokens: Max tokens for response
        max_turns: Maximum number of turns to prevent infinite loops
        verbose: Whether to print progress

    Returns:
        The final API response
    """
    turn = 1
    response = None

    while turn <= max_turns:
        if verbose:
            print(f"\n🔄 Turn {turn}:")

        response, assistant_content, tool_results = run_conversation_turn(
            client=client,
            model=model,
            messages=messages,
            memory_handler=memory_handler,
            system=system,
            context_management=context_management,
            max_tokens=max_tokens,
            verbose=verbose,
        )

        messages.append({"role": "assistant", "content": assistant_content})

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            turn += 1
        else:
            # No more tool uses, conversation complete
            break

    return response


def print_context_management_info(response: Any) -> tuple[bool, int]:
    """
    Print context management information from response.

    Args:
        response: API response to analyze

    Returns:
        Tuple of (context_cleared, saved_tokens)
    """
    context_cleared = False
    saved_tokens = 0

    if hasattr(response, "context_management") and response.context_management:
        edits = getattr(response.context_management, "applied_edits", [])
        if edits:
            context_cleared = True
            cleared_uses = getattr(edits[0], "cleared_tool_uses", 0)
            saved_tokens = getattr(edits[0], "cleared_input_tokens", 0)
            print("  ✂️  Context editing triggered!")
            print(f"      • Cleared {cleared_uses} tool uses")
            print(f"      • Saved {saved_tokens:,} tokens")
            print(f"      • After clearing: {response.usage.input_tokens:,} tokens")
        else:
            # Check if we can see why it didn't trigger
            skipped_edits = getattr(response.context_management, "skipped_edits", [])
            if skipped_edits:
                print("  ℹ️  Context clearing skipped:")
                for skip in skipped_edits:
                    reason = getattr(skip, "reason", "unknown")
                    print(f"      • Reason: {reason}")
            else:
                print("  ℹ️  Context below threshold - no clearing triggered")
    else:
        print("  ℹ️  No context management applied")

    return context_cleared, saved_tokens
