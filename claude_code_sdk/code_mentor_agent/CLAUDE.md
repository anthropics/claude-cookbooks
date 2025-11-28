# Code Mentor Agent

A Claude Code SDK agent that helps developers understand and improve their code through explanation, review, and best practices guidance.

## Agent Overview

The Code Mentor is designed to be a patient, knowledgeable guide for developers of all skill levels. It combines deep technical knowledge with clear explanations to help developers:

- **Understand** complex codebases and unfamiliar patterns
- **Review** code for bugs, security issues, and improvements
- **Learn** best practices and modern development techniques
- **Improve** code quality through actionable suggestions

## Available Subagents

### security-reviewer
Specializes in identifying security vulnerabilities including:
- Injection attacks (SQL, XSS, command injection)
- Authentication and authorization issues
- Data exposure and privacy concerns
- Dependency vulnerabilities

### performance-analyst
Focuses on performance optimization:
- Algorithm complexity analysis
- Memory and resource usage
- Database query optimization
- Caching opportunities

### architecture-advisor
Provides guidance on code structure:
- Design patterns and their applications
- SOLID principles adherence
- Code organization and modularity
- Refactoring strategies

## Custom Commands

- `/explain` - Get a detailed explanation of code
- `/review` - Perform a code review with findings
- `/improve` - Get actionable improvement suggestions
- `/security-scan` - Deep security analysis

## Output Styles

- **beginner** - Patient explanations with foundational concepts
- **expert** - Concise, technical, assumes deep knowledge

## Usage Examples

```python
from agent import send_query, explain_code, review_code

# General question
result = await send_query("What design pattern is used in src/factory.py?")

# Explain code
explanation = await explain_code("src/auth/login.py", detail_level="comprehensive")

# Review for security
review = await review_code("src/api/endpoints.py", focus="security")
```

## Best Practices for Using This Agent

1. **Provide context**: Point the agent to CLAUDE.md or README files first
2. **Be specific**: "Review the authentication flow in auth.py" > "Review auth"
3. **Use subagents**: For deep analysis, mention the specific subagent to use
4. **Iterate**: Start with explanation, then review, then improvements
