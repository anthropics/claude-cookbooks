---
allowed-tools: Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr review:*), Bash(git diff:*), Bash(git log:*), Task, Read, Glob, Grep
description: Review a pull request and post the review to GitHub (CI/automated use)
---

## Arguments

- `$ARGUMENTS`: The PR number to review

## Your task

Review the specified pull request and post a review to GitHub. This command is designed for CI/automated environments.

### Step 1: Gather PR context

Get the PR details and diff:
```
gh pr view $ARGUMENTS
gh pr diff $ARGUMENTS
```

### Step 2: Review the code changes

Use the Task tool with `subagent_type: "code-reviewer"` to perform a thorough code review of the changes. Pass the diff and changed files to the agent for analysis.

The code-reviewer agent will analyze:
- Code quality and best practices
- Potential bugs or issues
- Security concerns
- Performance considerations
- Documentation and comments

### Step 3: Determine review outcome

Based on the code review findings, determine the appropriate review action:
- **APPROVE** (`--approve`): Code looks good, no significant issues found
- **REQUEST_CHANGES** (`--request-changes`): Critical issues that must be fixed before merging
- **COMMENT** (`--comment`): Suggestions or minor issues that don't block merging

### Step 4: Post the review

Post the review to GitHub using:
```
gh pr review $ARGUMENTS --body "YOUR_REVIEW_BODY" --approve|--request-changes|--comment
```

Format your review body with:
- **Summary**: Brief overview of what the PR does
- **Findings**: Organized list of comments, suggestions, and issues
- **Line-specific feedback**: Format as `file:line - comment` for clarity

**Note for Jupyter notebooks:** Cell numbers are hard to identify, so when commenting on notebook code, include a snippet of the actual code or context to help locate the issue. For example, instead of "Cell 12, line 5", write "In the cell containing `financial_data_2024 = ...`" or include the relevant code snippet.

**Important:** The `gh pr review` command produces no output on success. Only run this command once - do not retry if there is no output, as that indicates success.
