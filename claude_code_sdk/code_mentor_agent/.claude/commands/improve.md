---
name: improve
description: Get actionable improvement suggestions - usage: /improve <file_path> [goal]
---

Suggest improvements for `$ARGUMENTS`.

The argument can be:
- Just a file path: `/improve src/app.py`
- File path with a goal: `/improve src/app.py reduce complexity`

## Improvement Process

1. **Analyze the current code** - Understand structure and purpose
2. **Identify improvement opportunities**:
   - Readability enhancements
   - Performance optimizations
   - Better patterns or abstractions
   - Reduced complexity
   - Improved error handling
   - Better naming
   - Documentation gaps

3. **Prioritize by impact** - Focus on high-value changes

## Output Format

```markdown
# Improvement Suggestions: [filename]

## Quick Wins
[Easy changes with immediate benefit]

### 1. [Improvement Title]
**Impact**: [High/Medium/Low]
**Effort**: [Low/Medium/High]

**Current**:
```code
// Current implementation
```

**Improved**:
```code
// Better implementation
```

**Why**: [Explanation of benefit]

---

## Larger Refactors
[More substantial improvements]

### 1. [Refactor Title]
**Impact**: [High/Medium/Low]
**Effort**: [Medium/High]

**Current Structure**:
[Description or diagram]

**Proposed Structure**:
[Description or diagram]

**Migration Steps**:
1. [Step 1]
2. [Step 2]

---

## Future Considerations
[Ideas for when the code evolves]

- [Consideration 1]
- [Consideration 2]
```

## Guidelines

- Prioritize impact over perfection
- Provide complete, working code examples
- Consider the effort required for each change
- Suggest incremental improvements, not rewrites
- Explain the "why" - what problem does the improvement solve?
- If a goal is specified, focus suggestions on that goal
