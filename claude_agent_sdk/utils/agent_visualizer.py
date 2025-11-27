from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    ToolUseBlock,
)


def print_activity(msg):
    if isinstance(msg, AssistantMessage):
        # Check if using a tool or just thinking
        if msg.content:
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"🤖 Using: {block.name}()")
                    return
        print("🤖 Thinking...")
    elif isinstance(msg, UserMessage):
        print("✓ Tool completed")


def print_final_result(messages):
    """Print the final agent result and cost information"""
    # Get the result message (last message)
    result_msg = messages[-1]

    # Find the last assistant message with actual content
    for msg in reversed(messages):
        if isinstance(msg, AssistantMessage) and msg.content:
            # Check if it has text content (not just tool use)
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"\n📝 Final Result:\n{block.text}")
                    break
            break

    # Print cost and duration if result message
    if isinstance(result_msg, ResultMessage):
        if result_msg.total_cost_usd:
            print(f"\n📊 Cost: ${result_msg.total_cost_usd:.2f}")
        if result_msg.duration_ms:
            print(f"⏱️  Duration: {result_msg.duration_ms / 1000:.2f}s")


def visualize_conversation(messages):
    """Create a visual representation of the entire agent conversation"""
    print("\n" + "=" * 60)
    print("🤖 AGENT CONVERSATION TIMELINE")
    print("=" * 60 + "\n")

    for i, msg in enumerate(messages):
        if isinstance(msg, SystemMessage):
            print("⚙️  System Initialized")
            if hasattr(msg, "data") and "session_id" in msg.data:
                print(f"   Session: {msg.data['session_id'][:8]}...")
            print()

        elif isinstance(msg, AssistantMessage):
            print("🤖 Assistant:")
            if msg.content:
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Text response
                        text = block.text[:500] + "..." if len(block.text) > 500 else block.text
                        print(f"   💬 {text}")
                    elif isinstance(block, ToolUseBlock):
                        # Tool use
                        tool_name = block.name
                        print(f"   🔧 Using tool: {tool_name}")

                        # Show key parameters for certain tools
                        if block.input:
                            if tool_name == "WebSearch" and "query" in block.input:
                                print(f'      Query: "{block.input["query"]}"')
                            elif tool_name == "TodoWrite" and "todos" in block.input:
                                todos = block.input["todos"]
                                in_progress = [t for t in todos if t["status"] == "in_progress"]
                                completed = [t for t in todos if t["status"] == "completed"]
                                print(
                                    f"      📋 {len(completed)} completed, {len(in_progress)} in progress"
                                )
            print()

        elif isinstance(msg, UserMessage):
            if msg.content and isinstance(msg.content, list):
                for result in msg.content:
                    if isinstance(result, dict) and result.get("type") == "tool_result":
                        print("👤 Tool Result Received")
                        tool_id = result.get("tool_use_id", "unknown")[:8]
                        print(f"   ID: {tool_id}...")

                        # Show result summary
                        if "content" in result:
                            content = result["content"]
                            if isinstance(content, str):
                                # Show more of the content
                                summary = content[:500] + "..." if len(content) > 500 else content
                                print(f"   📥 {summary}")
            print()

        elif isinstance(msg, ResultMessage):
            print("✅ Conversation Complete")
            if msg.num_turns:
                print(f"   Turns: {msg.num_turns}")
            if msg.total_cost_usd:
                print(f"   Cost: ${msg.total_cost_usd:.2f}")
            if msg.duration_ms:
                print(f"   Duration: {msg.duration_ms / 1000:.2f}s")
            if msg.usage:
                usage = msg.usage
                total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                print(f"   Tokens: {total_tokens:,}")
            print()

    print("=" * 60 + "\n")
