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

Format your review body using this template with collapsible sections:

```markdown
## PR Review

**Recommendation**: APPROVE | REQUEST_CHANGES | COMMENT

### Summary
[1-2 sentence overview of what this PR does]

<details>
<summary>Actionable Feedback (N items)</summary>

List specific items that need attention. Use checkboxes for trackable items:

- [ ] `file.py:42` - Description of issue or required change
- [ ] `notebook.ipynb` (in cell with `some_code = ...`) - Description
- [ ] General: Description of non-file-specific feedback

</details>

<details>
<summary>Detailed Review</summary>

### Code Quality
[Analysis of code patterns, readability, maintainability]

### Security
[Any security considerations or concerns]

### Suggestions
[Optional improvements that aren't blocking]

### Positive Notes
[What was done well - be specific]

</details>
```

**Guidelines:**
- Keep the summary and actionable feedback visible (outside collapsed sections)
- Put detailed analysis in the collapsed "Detailed Review" section to reduce noise
- Use checkboxes in actionable feedback so authors can track what they've addressed
- For Jupyter notebooks, reference code snippets instead of cell numbers (e.g., "in cell with `data = pd.read_csv(...)`")

**Important:** The `gh pr review` command produces no output on success. Only run this command once - do not retry if there is no output, as that indicates success.
