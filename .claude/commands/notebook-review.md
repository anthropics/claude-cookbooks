---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(echo:*),Read,Glob,Grep,WebFetch
description: Comprehensive review of Jupyter notebooks and Python scripts
---

**IMPORTANT**: Only review the files explicitly listed in the prompt above. Do not search for or review additional files.

Review the specified Jupyter notebooks and Python scripts using the Notebook review skill.

Provide a clear summary with:
- ✅ What looks good
- ⚠️ Suggestions for improvement
- ❌ Critical issues that must be fixed

**IMPORTANT: Post your review as a comment on the pull request using the command: `gh pr comment $PR_NUMBER --body "your review"`**
