---
name: review
description: Perform a code review with findings and recommendations - usage: /review <file_path or 'changes'>
---

Perform a thorough code review of `$ARGUMENTS`.

If the argument is "changes" or "diff", review the current git diff (staged and unstaged changes).
Otherwise, review the specified file.

## Review Process

1. **Read the code** - Understand what it does
2. **Check for issues** in these categories:
   - **Bugs**: Logic errors, off-by-one, null checks, edge cases
   - **Security**: Injection, auth issues, data exposure (use security-reviewer subagent for deep analysis)
   - **Performance**: Inefficient algorithms, N+1 queries, memory issues
   - **Maintainability**: Complexity, naming, documentation, DRY violations
   - **Style**: Consistency, formatting, conventions

3. **Prioritize findings** by impact and severity

## Output Format

```markdown
# Code Review: [filename]

## Summary
[1-2 sentence overview of code quality]

## Findings

### Critical
[Issues that must be fixed - bugs, security vulnerabilities]

### Important
[Issues that should be fixed - performance, maintainability]

### Suggestions
[Nice-to-have improvements]

## Detailed Findings

### [SEVERITY] [Title]
**Location**: line X
**Issue**: [Description]
**Suggestion**:
```code
// Improved code
```

## What's Done Well
- [Positive observation]
- [Another positive]

## Overall Assessment
[Brief conclusion and recommended next steps]
```

## Guidelines

- Be constructive - explain why, not just what
- Provide working code fixes
- Acknowledge good practices, not just problems
- Consider context - internal vs external code
- Don't nitpick style unless it hurts readability
