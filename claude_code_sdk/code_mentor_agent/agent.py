#!/usr/bin/env python3
"""
Code Mentor Agent - A Claude Code SDK agent that helps developers understand
and improve codebases through code review, explanation, and best practices guidance.

This agent demonstrates:
- Multi-agent orchestration with specialized subagents
- Custom slash commands for common workflows
- Activity tracking and progress reporting
- Working directory context for code analysis
"""

import asyncio
import os
from collections.abc import Callable
from typing import Any, Literal

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from dotenv import load_dotenv

load_dotenv()

# Default model for the agent
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def get_activity_text(msg: Any) -> str | None:
    """
    Extract human-readable activity text from SDK messages.

    Args:
        msg: A message from the Claude SDK response stream

    Returns:
        A formatted string describing the activity, or None if not applicable
    """
    try:
        class_name = msg.__class__.__name__

        if "Assistant" in class_name:
            if hasattr(msg, "content") and msg.content:
                first_content = msg.content[0] if isinstance(msg.content, list) else msg.content

                # Tool use
                if hasattr(first_content, "name"):
                    tool_name = first_content.name
                    tool_icons = {
                        "Read": "📖",
                        "Grep": "🔍",
                        "Glob": "📂",
                        "Bash": "⚡",
                        "WebSearch": "🌐",
                        "Task": "🤖",
                        "Edit": "✏️",
                        "Write": "📝",
                    }
                    icon = tool_icons.get(tool_name, "🔧")
                    return f"{icon} Using: {tool_name}()"

                # Text response
                if hasattr(first_content, "text"):
                    text = first_content.text[:50]
                    return f"💭 Thinking: {text}..."

            return "🤔 Processing..."

        elif "User" in class_name:
            return "✅ Tool completed"

        elif "Result" in class_name:
            return "🎯 Analysis complete"

    except (AttributeError, IndexError, TypeError):
        pass

    return None


def print_activity(msg: Any) -> None:
    """Print activity updates to console with formatting."""
    activity = get_activity_text(msg)
    if activity:
        print(f"  {activity}")


async def send_query(
    prompt: str,
    activity_handler: Callable[[Any], None | Any] = print_activity,
    continue_conversation: bool = False,
    cwd: str | None = None,
    permission_mode: Literal["default", "plan", "acceptEdits"] = "default",
    output_style: str | None = None,
) -> str | None:
    """
    Send a query to the Code Mentor agent.

    This function initializes the agent with appropriate tools and configuration,
    then streams the response while tracking activity.

    Args:
        prompt: The question or task for the agent
        activity_handler: Callback for activity updates (default: print_activity)
        continue_conversation: If True, maintains context from previous queries
        cwd: Working directory for code analysis (defaults to agent directory)
        permission_mode: "default" (execute), "plan" (think only), "acceptEdits"
        output_style: Optional output style (e.g., "beginner", "expert")

    Returns:
        The final result text, or None if no result

    Example:
        >>> result = await send_query(
        ...     "Explain the main function in src/app.py",
        ...     cwd="/path/to/project"
        ... )
    """
    # Build system prompt
    system_prompt = """You are a Code Mentor - an expert software engineering guide who helps
developers understand and improve their code. You combine deep technical knowledge with
clear, patient explanations.

## Your Capabilities

1. **Code Explanation**: Break down complex code into understandable concepts
2. **Code Review**: Identify bugs, security issues, and areas for improvement
3. **Best Practices**: Recommend patterns, standards, and modern approaches
4. **Architecture Guidance**: Help with design decisions and code organization

## Your Approach

- Start by understanding the context and the developer's experience level
- Use the codebase context in CLAUDE.md when available
- Leverage your specialized subagents for deep analysis:
  - `security-reviewer`: For security vulnerability analysis
  - `performance-analyst`: For optimization opportunities
  - `architecture-advisor`: For design patterns and structure

## Communication Style

- Be encouraging but honest - point out issues constructively
- Provide concrete examples and actionable suggestions
- Explain the "why" behind recommendations
- Adapt complexity to the developer's level
"""

    # Configure options
    options_dict = {
        "model": DEFAULT_MODEL,
        "allowed_tools": [
            "Read",       # Read code files
            "Glob",       # Find files by pattern
            "Grep",       # Search code content
            "Bash",       # Run analysis tools (linters, tests)
            "WebSearch",  # Look up best practices
            "Task",       # Delegate to subagents
        ],
        "system_prompt": system_prompt,
        "continue_conversation": continue_conversation,
        "permission_mode": permission_mode,
        "cwd": cwd or os.path.dirname(os.path.abspath(__file__)),
    }

    # Add output style if specified
    if output_style:
        options_dict["settings"] = f'{{"outputStyle": "{output_style}"}}'

    options = ClaudeCodeOptions(**options_dict)

    result = None

    try:
        async with ClaudeSDKClient(options=options) as agent:
            await agent.query(prompt=prompt)

            async for msg in agent.receive_response():
                # Handle activity callback
                if asyncio.iscoroutinefunction(activity_handler):
                    await activity_handler(msg)
                else:
                    activity_handler(msg)

                # Capture final result
                if hasattr(msg, "result"):
                    result = msg.result

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    return result


async def explain_code(
    file_path: str,
    cwd: str | None = None,
    detail_level: Literal["brief", "detailed", "comprehensive"] = "detailed",
) -> str | None:
    """
    Explain a code file or specific section.

    Args:
        file_path: Path to the file to explain (relative to cwd)
        cwd: Working directory containing the code
        detail_level: How detailed the explanation should be

    Returns:
        Explanation of the code
    """
    prompts = {
        "brief": f"Give a brief overview of what {file_path} does in 2-3 sentences.",
        "detailed": f"Explain the code in {file_path}. Cover the main components, "
                   f"how they work together, and any notable patterns or techniques used.",
        "comprehensive": f"Provide a comprehensive explanation of {file_path}. Include: "
                        f"1) Purpose and context, 2) Main components and their roles, "
                        f"3) Data flow and logic, 4) Design patterns used, "
                        f"5) Dependencies and interactions with other code."
    }

    return await send_query(prompts[detail_level], cwd=cwd)


async def review_code(
    file_path: str | None = None,
    cwd: str | None = None,
    focus: Literal["all", "security", "performance", "style"] = "all",
) -> str | None:
    """
    Review code for issues and improvements.

    Args:
        file_path: Specific file to review, or None for recent changes
        cwd: Working directory containing the code
        focus: What aspect to focus the review on

    Returns:
        Code review with findings and recommendations
    """
    focus_prompts = {
        "all": "Review for bugs, security issues, performance, and code style.",
        "security": "Focus specifically on security vulnerabilities and risks. "
                   "Use the security-reviewer subagent for deep analysis.",
        "performance": "Focus on performance issues and optimization opportunities. "
                      "Use the performance-analyst subagent for detailed analysis.",
        "style": "Focus on code style, readability, and maintainability."
    }

    if file_path:
        prompt = f"Review the code in {file_path}. {focus_prompts[focus]}"
    else:
        prompt = f"Review recent code changes (git diff). {focus_prompts[focus]}"

    return await send_query(prompt, cwd=cwd)


async def suggest_improvements(
    file_path: str,
    cwd: str | None = None,
    goal: str | None = None,
) -> str | None:
    """
    Suggest improvements for a code file.

    Args:
        file_path: Path to the file to improve
        cwd: Working directory containing the code
        goal: Specific improvement goal (e.g., "reduce complexity", "add tests")

    Returns:
        Improvement suggestions with examples
    """
    if goal:
        prompt = f"Suggest improvements for {file_path} with the goal: {goal}. "
    else:
        prompt = f"Suggest improvements for {file_path}. "

    prompt += ("Provide specific, actionable suggestions with code examples. "
               "Prioritize by impact and explain the benefits of each change.")

    return await send_query(prompt, cwd=cwd)


# Main entry point for command-line usage
if __name__ == "__main__":
    import sys

    print("🎓 Code Mentor Agent")
    print("=" * 40)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What can you help me with as a Code Mentor?"

    print(f"\n📝 Query: {query}\n")

    result = asyncio.run(send_query(query))

    if result:
        print("\n" + "=" * 40)
        print("📋 Result:")
        print(result)
