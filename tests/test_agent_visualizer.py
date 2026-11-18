from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

SDK_COOKBOOK_DIR = Path(__file__).resolve().parent.parent / "claude_agent_sdk"
if str(SDK_COOKBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_COOKBOOK_DIR))

from utils.agent_visualizer import (  # noqa: E402
    print_activity,
    reset_activity_context,
    visualize_conversation,
)


def _assistant(blocks: list, parent_tool_use_id: str | None = None) -> AssistantMessage:
    return AssistantMessage(
        content=blocks,
        model="claude-opus-5-5",
        parent_tool_use_id=parent_tool_use_id,
    )


def test_print_activity_tracks_subagent_lifecycle_with_sdk_blocks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reset_activity_context()

    print_activity(
        _assistant(
            [
                TextBlock(text="Delegating hiring analysis."),
                ToolUseBlock(
                    id="toolu_agent_1",
                    name="Agent",
                    input={
                        "subagent_type": "financial-analyst",
                        "description": "Analyze hiring impact",
                    },
                ),
            ]
        )
    )
    print_activity(
        _assistant(
            [ToolUseBlock(id="toolu_bash_1", name="Bash", input={"command": "python calc.py"})],
            parent_tool_use_id="toolu_agent_1",
        )
    )
    print_activity(
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_bash_1",
                    content="subagent helper script output",
                    is_error=False,
                )
            ],
            parent_tool_use_id="toolu_agent_1",
        )
    )
    print_activity(
        _assistant(
            [ToolUseBlock(id="toolu_read_1", name="Read", input={"file_path": "budget.csv"})],
            parent_tool_use_id="toolu_agent_1",
        )
    )
    print_activity(
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_read_1",
                    content="row1,row2",
                    is_error=False,
                )
            ],
            parent_tool_use_id="toolu_agent_1",
        )
    )
    print_activity(
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_agent_1",
                    content=[{"type": "text", "text": "Runway drops by 1.8 months."}],
                    is_error=False,
                )
            ]
        )
    )
    print_activity(_assistant([TextBlock(text="Here is the combined recommendation.")]))

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines == [
        "🚀 Delegating to subagent: financial-analyst",
        "   └─ Task: Analyze hiring impact",
        "   📎 [financial-analyst] Using: Bash()",
        "   ✓ Tool completed",
        "   📎 [financial-analyst] Using: Read()",
        "   ✓ Tool completed",
        "   ✅ Subagent [financial-analyst] completed",
        "🤖 Thinking...",
    ]


def test_print_activity_dict_inner_tool_result_does_not_close_subagent_early(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reset_activity_context()

    print_activity(
        _assistant(
            [
                ToolUseBlock(
                    id="toolu_task_1",
                    name="Task",
                    input={"subagent_type": "recruiter"},
                )
            ]
        )
    )
    print_activity(
        UserMessage(
            content=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_inner_1",
                    "content": "subagent candidate list loaded",
                }
            ]
        )
    )
    print_activity(
        _assistant(
            [ToolUseBlock(id="toolu_bash_2", name="Bash", input={"command": "python score.py"})]
        )
    )
    print_activity(
        UserMessage(
            content=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_task_1",
                    "content": "Top candidate scored 88.",
                }
            ]
        )
    )
    print_activity(_assistant([TextBlock(text="Done.")]))

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines == [
        "🚀 Delegating to subagent: recruiter",
        "   ✓ Tool completed",
        "   📎 [recruiter] Using: Bash()",
        "   ✅ Subagent [recruiter] completed",
        "🤖 Thinking...",
    ]


def test_visualize_conversation_terminal_closes_subagent_on_sdk_tool_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    messages = [
        SystemMessage(
            subtype="init", data={"session_id": "sess_12345678", "model": "claude-opus-5-5"}
        ),
        _assistant(
            [
                ToolUseBlock(
                    id="toolu_agent_1",
                    name="Agent",
                    input={
                        "subagent_type": "financial-analyst",
                        "description": "Check burn",
                        "prompt": "Compute burn impact",
                    },
                )
            ]
        ),
        _assistant(
            [ToolUseBlock(id="toolu_read_1", name="Read", input={"file_path": "data/burn.csv"})],
            parent_tool_use_id="toolu_agent_1",
        ),
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_read_1",
                    content="x" * 300,
                    is_error=False,
                )
            ],
            parent_tool_use_id="toolu_agent_1",
        ),
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_agent_1",
                    content="Short summary from subagent.",
                    is_error=False,
                )
            ]
        ),
        _assistant([TextBlock(text="Final answer from main agent.")]),
        ResultMessage(
            subtype="success",
            duration_ms=1200,
            duration_api_ms=1000,
            is_error=False,
            num_turns=2,
            session_id="sess_12345678",
            total_cost_usd=0.05,
            usage={"input_tokens": 100, "output_tokens": 50},
            result="Final answer from main agent.",
        ),
    ]

    with patch("utils.agent_visualizer._is_jupyter", return_value=False):
        visualize_conversation(messages)

    out = capsys.readouterr().out
    subagent_complete_pos = out.find("SUBAGENT [FINANCIAL-ANALYST] COMPLETE")
    subagent_summary_pos = out.find("Short summary from subagent.")
    main_assistant_pos = out.find("🤖 Assistant:\n   Final answer from main agent.")

    assert subagent_complete_pos != -1
    assert subagent_summary_pos != -1
    assert main_assistant_pos != -1
    assert subagent_complete_pos < main_assistant_pos
    assert "x" * 300 not in out


def test_print_activity_parallel_subagents_match_by_tool_use_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reset_activity_context()

    print_activity(
        _assistant(
            [
                ToolUseBlock(
                    id="toolu_fin",
                    name="Agent",
                    input={"subagent_type": "financial-analyst"},
                ),
                ToolUseBlock(
                    id="toolu_rec",
                    name="Agent",
                    input={"subagent_type": "recruiter"},
                ),
            ]
        )
    )
    print_activity(
        _assistant(
            [ToolUseBlock(id="toolu_b1", name="Bash", input={"command": "python forecast.py"})],
            parent_tool_use_id="toolu_fin",
        )
    )
    print_activity(
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_fin",
                    content="Financial report ready.",
                    is_error=False,
                )
            ]
        )
    )
    print_activity(
        _assistant(
            [ToolUseBlock(id="toolu_b2", name="Bash", input={"command": "python score.py"})],
            parent_tool_use_id="toolu_rec",
        )
    )
    print_activity(
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="toolu_rec",
                    content="Candidate report ready.",
                    is_error=False,
                )
            ]
        )
    )
    print_activity(_assistant([TextBlock(text="Both subagents finished.")]))

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines == [
        "🚀 Delegating to subagent: financial-analyst",
        "🚀 Delegating to subagent: recruiter",
        "      📎 [financial-analyst] Using: Bash()",
        "      ✅ Subagent [financial-analyst] completed",
        "   📎 [recruiter] Using: Bash()",
        "   ✅ Subagent [recruiter] completed",
        "🤖 Thinking...",
    ]
