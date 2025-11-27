---
allowed-tools: Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue comment:*), Bash(gh issue edit:*), Bash(gh issue close:*), Read, Glob, Grep, AskUserQuestion
description: Review and respond to a GitHub issue
---

## Arguments

- `$ARGUMENTS`: The issue number to review

## Your task

Review the specified GitHub issue and help draft an appropriate response based on our community guidelines.

### Step 1: Gather issue context

Get the issue details including comments:
```bash
gh issue view $ARGUMENTS --repo anthropics/claude-cookbooks --json number,title,body,author,labels,state,comments,createdAt
```

### Step 2: Classify the issue

Determine the issue type based on content:

1. **Spam/Noise**: Gibberish, test posts, off-topic content, or malicious intent
2. **Bug Report**: Reports broken code, links, or incorrect information in cookbooks
3. **Cookbook Proposal**: Proposes new content or significant additions
4. **Question**: Asks about usage, API behavior, or seeks clarification
5. **Community Resource**: Shares external project or resource (redirect to Discord)
6. **Duplicate**: Issue already exists or has been addressed

### Step 3: Check for related context

If the issue references specific files or notebooks:
- Read the referenced files to understand context
- Check if the issue is valid (e.g., broken link actually exists)
- Look for related issues or PRs that may address it

### Step 4: Draft a response

Based on the issue type, draft an appropriate response following these guidelines:

#### For Spam/Noise:
- Recommend closing without comment
- Flag any security concerns

#### For Bug Reports:
- Acknowledge the report and thank the reporter
- Verify the issue if possible (check the referenced file/code)
- If valid and simple: invite them to submit a PR with signed commits
- If valid and complex: acknowledge and indicate it's on our radar
- If already fixed: reference the fix (PR/commit)
- Example: "Thanks for the report! Would you be open to submitting a PR to fix this? If so, please ensure you use [signed commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)"

#### For Cookbook Proposals:
- Thank them for the proposal
- Evaluate against our criteria:
  - Does it focus on Claude API/SDK capabilities directly?
  - Is it practical with clear educational value?
  - Is it differentiated from existing content?
- If promising: express interest, ask clarifying questions if needed
- If not a fit: politely explain why, redirect to appropriate resources
- Example redirect: "While [topic] is interesting, we focus on showcasing Claude's native API capabilities. We'd encourage you to think about what specific Claude features you want to demonstrate rather than translating patterns from external frameworks."

#### For Questions:
- Provide helpful, direct answers when possible
- Link to relevant documentation: https://docs.claude.com
- Reference specific cookbook examples if applicable
- Suggest Discord for ongoing discussion: https://anthropic.com/discord
- If it's an API bug: direct them to report at the appropriate channel

#### For Community Resources:
- Thank them for sharing but redirect to better venues
- This repo is for cookbook issues, not community showcases
- Close the issue after redirecting
- Example: "Thanks for sharing your project! We don't track community resources as GitHub issues, but there are great places to share your work: the **#share-your-project** channel on our [Discord](https://anthropic.com/discord) or the [r/ClaudeAI](https://reddit.com/r/ClaudeAI) community on Reddit."

#### For Duplicates:
- Reference the original issue/PR
- Close as duplicate if appropriate

### Step 5: Suggest labels

Recommend appropriate labels based on issue type:
- `bug` - Bug reports
- `enhancement` - Feature requests or proposals
- `question` - Questions
- `documentation` - Docs improvements
- `duplicate` - Already exists
- `wontfix` - Won't be addressed
- `good first issue` - Simple fixes for new contributors

### Step 6: Present the review

Present your findings to the user:

1. **Issue Summary**: Brief description of what the issue is about
2. **Classification**: What type of issue this is
3. **Validity Check**: Whether the issue is valid/actionable (if you checked)
4. **Suggested Response**: Draft comment to post
5. **Suggested Labels**: Labels to add
6. **Suggested Action**: Whether to comment, close, or take other action

### Step 7: Get user approval

Use AskUserQuestion to ask:
- Whether to post the drafted response
- Whether to add the suggested labels
- Whether to close the issue (if appropriate)

### Step 8: Take action (if approved)

Based on user approval:

**To post a comment:**
```bash
gh issue comment $ARGUMENTS --repo anthropics/claude-cookbooks --body "YOUR_RESPONSE"
```

**To add labels:**
```bash
gh issue edit $ARGUMENTS --repo anthropics/claude-cookbooks --add-label "label1,label2"
```

**To close an issue:**
```bash
gh issue close $ARGUMENTS --repo anthropics/claude-cookbooks --reason "not planned"
```
Or with a comment:
```bash
gh issue close $ARGUMENTS --repo anthropics/claude-cookbooks --comment "Closing because..."
```

## Response Tone Guidelines

- Be professional, friendly, and concise
- Thank contributors for their engagement
- Be direct but not dismissive when declining proposals
- Provide actionable next steps when possible
- Link to resources rather than explaining everything inline
- Don't over-explain or be overly apologetic

## Example Responses

**Bug Report Response:**
```
Hi @username, thanks for the detailed report!

I can confirm the link is broken. Would you be open to submitting a PR to fix this? If so, please ensure you use [signed commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

If you'd prefer not to submit a PR, no worries - we'll get this fixed.
```

**Question Response:**
```
Hi @username!

The `cache_control` parameter is needed because... [explanation]

For more details, check out the [prompt caching documentation](https://docs.claude.com/en/docs/build-with-claude/prompt-caching).

If you have follow-up questions, our [Discord](https://anthropic.com/discord) is a great place for discussion!
```

**Proposal Decline Response:**
```
Hi @username, thanks for the detailed proposal!

While the concept is interesting, we focus our cookbooks on demonstrating Claude's native API capabilities directly. We'd encourage you to consider:

- What specific Claude API features are you showcasing?
- How is this differentiated from existing documentation?
- Can users run this self-contained without external dependencies?

If you can reframe the proposal around these questions, we'd be happy to reconsider. Thanks for your engagement with the SDK!
```
