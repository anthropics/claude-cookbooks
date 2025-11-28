---
allowed-tools: Read,Glob,Grep,Edit
description: Add a new notebook to registry.yaml
---

Add a new entry to `registry.yaml` for the notebook specified in the prompt above.

## Instructions

1. **Read the notebook** at the specified path to understand its content
2. **Check author exists** in `authors.yaml`:
   - Ask the user for the GitHub username of the notebook author
   - Read `authors.yaml` and check if that username exists as a key
   - If the author does NOT exist, ask the user for their details and add them to `authors.yaml`:
     - **name**: Full display name
     - **website**: GitHub profile URL or personal website
     - **avatar**: Use `https://github.com/<username>.png` as default
3. **Generate the registry entry** with these fields:

### Required Fields
- **title**: Extract from the notebook's first heading or create a concise, descriptive title
- **description**: Write a brief 1-2 sentence description summarizing what the notebook teaches
- **path**: The notebook path relative to the repository root
- **authors**: Use the GitHub username from step 2
- **date**: Use today's date in YYYY-MM-DD format
- **categories**: Select 1-2 appropriate categories from this list:
  - Agent Patterns
  - Claude Agent SDK
  - Evals
  - Fine-Tuning
  - Multimodal
  - Integrations
  - Observability
  - RAG & Retrieval
  - Responses
  - Skills
  - Thinking
  - Tools

### Style Guidelines
- Title should be concise but descriptive (see existing entries for examples)
- Description should be ~15-20 words, focusing on what the user will learn/build
- Choose categories that best match the notebook's primary focus

## Output

1. If author is new, show the proposed `authors.yaml` entry for review and add it after approval
2. Show the user the proposed `registry.yaml` entry for review
3. After user approval, use the Edit tool to append the entry to `registry.yaml`
4. Maintain alphabetical ordering by path within the file, or append to the end if unclear

## Example Entry Formats

### authors.yaml (only if new author)
```yaml
github-username:
  name: Full Name
  website: https://github.com/github-username
  avatar: https://github.com/github-username.png
```

### registry.yaml
```yaml
- title: Example Notebook Title
  description: Brief description of what this notebook covers and teaches users.
  path: category/notebook_name.ipynb
  authors:
  - github-username
  date: 'YYYY-MM-DD'
  categories:
  - Category Name
```
