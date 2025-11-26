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

After the code review is complete, present the review to the user using this format:

```
## PR Review

**Recommendation**: APPROVE | REQUEST_CHANGES | COMMENT

### Summary
[1-2 sentence overview of what this PR does]

### Actionable Feedback (N items)
- [ ] `file.py:42` - Description of issue or required change
- [ ] `notebook.ipynb` (in cell with `some_code = ...`) - Description

### Detailed Review

#### Code Quality
[Analysis of code patterns, readability, maintainability]

#### Security
[Any security considerations]

#### Suggestions
[Optional improvements]

#### Positive Notes
[What was done well]
```

**Guidelines:**
- Use checkboxes for actionable items so authors can track progress
- For Jupyter notebooks, reference code snippets instead of cell numbers
- Be specific with file:line references where possible

### Step 5: Ask about posting the review

Use the AskUserQuestion tool to ask the user:
- Whether they want to post this review to GitHub
- What review action to take: APPROVE, REQUEST_CHANGES, or COMMENT

### Step 6: Post the review (if approved)

If the user confirms, post the review using:
```
gh pr review $ARGUMENTS --body "YOUR_REVIEW_BODY" --approve|--request-changes|--comment
```

When posting to GitHub, wrap the Detailed Review section in a collapsible `<details>` tag to reduce noise:

```markdown
## PR Review

**Recommendation**: APPROVE | REQUEST_CHANGES | COMMENT

### Summary
[summary]

<details>
<summary>Actionable Feedback (N items)</summary>

- [ ] items...

</details>

<details>
<summary>Detailed Review</summary>

[full review content]

</details>
```

Use the appropriate flag based on the user's choice:
- `--approve` for APPROVE
- `--request-changes` for REQUEST_CHANGES
- `--comment` for COMMENT only

**Important:** The `gh pr review` command produces no output on success. Only run this command once - do not retry if there is no output, as that indicates success.
