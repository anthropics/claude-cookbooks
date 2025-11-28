---
name: explain
description: Get a detailed explanation of code - usage: /explain <file_path>
---

Explain the code in `$ARGUMENTS` in a clear, educational way.

## Your Task

1. **Read the file** using the Read tool
2. **Understand the context** - check for related files, imports, and dependencies
3. **Explain the code** covering:
   - **Purpose**: What does this code do? What problem does it solve?
   - **Structure**: How is it organized? What are the main components?
   - **Logic Flow**: Walk through the key algorithms or processes
   - **Patterns**: What design patterns or techniques are used?
   - **Dependencies**: What does it depend on? What depends on it?

## Output Format

```markdown
# Explanation: [filename]

## Purpose
[1-2 sentences on what this code does]

## Key Components

### [Component 1]
[Explanation]

### [Component 2]
[Explanation]

## How It Works
[Step-by-step flow of the main logic]

## Notable Patterns
- [Pattern]: [Why it's used here]

## Questions to Consider
- [Thought-provoking question about the code]
```

## Guidelines

- Adapt complexity to the code - simple code needs simple explanations
- Use analogies when explaining complex concepts
- Highlight any clever or non-obvious techniques
- Point out potential gotchas or edge cases
- If the code has issues, mention them constructively
