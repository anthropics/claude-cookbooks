---
allowed-tools: Bash(gh pr checkout:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr review:*), Bash(git diff:*), Bash(git log:*), Task, Read, Glob, Grep, AskUserQuestion
description: Review an open pull request and optionally post the review to GitHub
---

## Arguments

- `$ARGUMENTS`: The PR number or URL to review

## Your task

Review the specified pull request and provide feedback.

### Step 1: Checkout the PR

First, checkout the PR using:
```
gh pr checkout $ARGUMENTS
```

### Step 2: Gather PR context

Get the PR details:
```
gh pr view $ARGUMENTS
gh pr diff $ARGUMENTS
```

### Step 3: Review the code changes

Use the Task tool with `subagent_type: "code-reviewer"` to perform a thorough code review of the changes. Pass the diff and changed files to the agent for analysis.

The code-reviewer agent will analyze:
- Code quality and best practices
- Potential bugs or issues
- Security concerns
- Performance considerations
- Documentation and comments

### Step 4: Present the review

After the code review is complete, present a summary of the review to the user with:
- **Overall assessment**: Approve, Request Changes, or Comment
- **Summary**: Brief overview of the changes
- **Detailed findings**: List of specific comments, suggestions, and issues found
- **Line-specific comments**: Format these as `file:line - comment` for clarity

**Note for Jupyter notebooks:** Cell numbers are hard to identify, so when commenting on notebook code, include a snippet of the actual code or context to help locate the issue. For example, instead of "Cell 12, line 5", write "In the cell containing `financial_data_2024 = ...`" or include the relevant code snippet.

### Step 5: Ask about posting the review

Use the AskUserQuestion tool to ask the user:
- Whether they want to post this review to GitHub
- What review action to take: APPROVE, REQUEST_CHANGES, or COMMENT

### Step 6: Post the review (if approved)

If the user confirms, post the review using:
```
gh pr review $ARGUMENTS --body "YOUR_REVIEW_BODY" --approve|--request-changes|--comment
```

Use the appropriate flag based on the user's choice:
- `--approve` for APPROVE
- `--request-changes` for REQUEST_CHANGES
- `--comment` for COMMENT only

**Important:** The `gh pr review` command produces no output on success. Only run this command once - do not retry if there is no output, as that indicates success.
