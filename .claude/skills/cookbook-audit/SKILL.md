---
name: cookbook-audit
description: Audit an Anthropic Cookbook notebook based on a rubric. Use whenever a notebook review or audit is requested.
---

# Cookbook Audit

## Instructions

Review the requested Cookbook notebook using the following guidelines. Provide a score based on scoring guidelines and recommendations on improving the cookbook.

## Workflow

Follow these steps for a comprehensive audit:

1. **Identify the notebook**: Ask user for path if not provided
2. **Run automated checks**: Use `python3 validate_notebook.py <path>` to catch technical issues and generate markdown
   - The script automatically runs detect-secrets to scan for hardcoded API keys and credentials
   - Uses custom patterns defined in `scripts/detect-secrets/plugins.py`
   - Checks against baseline at `scripts/detect-secrets/.secrets.baseline`
3. **Review markdown output**: The script generates a markdown file in the `tmp/` folder for easier review (saves context vs raw .ipynb)
   - The tmp/ folder is gitignored to avoid committing review artifacts
   - Markdown includes code cells but excludes outputs for cleaner review
4. **Manual review**: Read through the markdown version evaluating against rubric
5. **Score each dimension**: Apply scoring guidelines objectively
6. **Generate report**: Follow the audit report format below
7. **Provide specific examples**: Show concrete improvements with line references

## Audit Report Format

Present your audit using this structure:

### Executive Summary
- **Overall Score**: X/20
- **Key Strengths** (2-3 bullet points)
- **Critical Issues** (2-3 bullet points)

### Detailed Scoring

#### 1. Narrative Quality: X/5
[Brief justification with specific examples]

#### 2. Code Quality: X/5
[Brief justification with specific examples]

#### 3. Technical Accuracy: X/5
[Brief justification with specific examples]

#### 4. Actionability & Understanding: X/5
[Brief justification with specific examples]

### Specific Recommendations

[Prioritized, actionable list of improvements with references to specific sections]

### Examples & Suggestions

[Show specific excerpts from the notebook with concrete suggestions for improvement]

## Quick Reference Checklist

Use this to ensure comprehensive coverage:

**Structure & Organization**
- [ ] Has clear introduction (1-2 paragraphs)
- [ ] States problem, audience, and outcome
- [ ] Lists prerequisites clearly
- [ ] Has logical section progression
- [ ] Includes conclusion/summary

**Code Quality**
- [ ] All code blocks have explanatory text before them
- [ ] No hardcoded API keys (automatically checked by detect-secrets)
- [ ] Meaningful variable names
- [ ] Comments explain "why" not "what"
- [ ] Follows language best practices
- [ ] Model name defined as constant at top of notebook

**Output Management**
- [ ] pip install logs suppressed with %%capture
- [ ] No verbose debug output
- [ ] Shows relevant API responses
- [ ] Stack traces only when demonstrating error handling

**Content Quality**
- [ ] Explains why approaches work
- [ ] Discusses when to use this approach
- [ ] Mentions limitations/considerations
- [ ] Provides transferable knowledge
- [ ] Appropriate model selection

**Technical Requirements**
- [ ] Executable without modification (except API keys)
- [ ] Uses non-deprecated API patterns
- [ ] Uses valid model names (claude-sonnet-4-5, claude-haiku-4-5, claude-opus-4-1)
- [ ] Model name defined as constant at top of notebook
- [ ] Includes dependency specifications
- [ ] Assigned to primary category
- [ ] Has relevant tags

### Content Philosophy: Action + Understanding

Cookbooks are primarily action-oriented but strategically incorporate understanding and informed by Diataxis framework.

Practical focus: Show users how to accomplish specific tasks with working code
Builder's perspective: Written from the user's point of view, solving real problems
Agency-building: Help users understand why approaches work, not just how
Transferable knowledge: Teach patterns and principles that apply beyond the specific example
Critical thinking: Encourage users to question outputs, recognize limitations, make informed choices

### What Makes a Good Cookbook

A good cookbook doesn't just help users solve today's problem, it also helps them understand the underlying principles behind the solutions, encouraging them to recognize when and how to adapt approaches. Users will be able to make more informed decisions about AI system design, develop judgement about model outputs, and build skills that transfer to future AI systems.

### What Cookbooks Are NOT

Cookbooks are not pure tutorials: We assume users have basic technical skills and API familiarity. We clearly state prerequisites in our cookbooks, and direct users to the Academy to learn more on topics.
They are not comprehensive explanations: We don't teach transformer architecture or probability theory. We need to understand that our users are following our cookbooks to solve problems they are facing today. They are busy, in the midst of learning or building, and want to be able to use what they learn to solve their immediate needs.
Cookbooks are not reference docs: We don't exhaustively document every parameter, we link to appropriate resources in our documentation as needed.
Cookbooks are not simple tips and tricks: We don't teach "hacks" that only work for the current model generation. We don't over-promise and under-deliver.
Cookbooks are not production-ready code: They showcase use cases and capabilities, not production patterns. Excessive error handling is not required.

### Style Guidelines

#### Voice & Tone

Educational and agency-building
Professional but approachable
Respectful of user intelligence and time
Either second person ("you") or first person plural ("we") - be consistent within a notebook

#### Writing Quality

Clear, concise explanations
Active voice preferred
Short paragraphs (3-5 sentences)
Avoid jargon without definition
Use headers to break up sections

#### Code Presentation

Every code block should be preceded by explanatory text
Comments should explain why, not what
Use meaningful variable names

#### Output Handling
Remove extraneous output, e.g with %%capture
pip install logs
Verbose debug statements
Lengthy stack traces (unless demonstrating error handling)
Show relevant output:
API responses that demonstrate functionality
Examples of successful execution

### Structural Requirements

Required Sections

1. Introduction (Required)
[Cookbook Title]

[1-2 paragraphs covering:]
- What problem this solves
- Who this is for
- What you'll build/accomplish

 Prerequisites
- Required technical skills
- API keys needed
- Dependencies to install

2. Main Content (Required)
Organized by logical steps or phases, each with:
Clear section headers
Explanatory text before code blocks
Code examples
Expected outputs (where relevant)
Understanding callouts: Brief explanations of why approaches work, when to use them, or important considerations

3. Conclusion (Recommended)

Summary of what was accomplished
Limitations or considerations
Next steps or related resources

Optional Sections
How It Works: Brief explanation of the underlying approach or mechanism
When to Use This: Guidance on appropriate use cases and contexts
Limitations & Considerations: Important caveats, failure modes, or constraints
Troubleshooting: Common issues and solutions
Variations: Alternative approaches or extensions
Performance Notes: Optimization considerations
Further Reading: Links to relevant docs, papers, or deeper explanations

## Examples

### Example 1: High-Quality Notebook Audit (Score: 18/20)

**Notebook**: "Building a Customer Support Agent with Tool Use"

#### Executive Summary
- **Overall Score**: 18/20
- **Key Strengths**:
  - Excellent narrative flow from problem to solution
  - Clean, well-documented code with proper error handling
  - Strong focus on transferable patterns (tool schema design, error recovery)
- **Critical Issues**:
  - Missing %%capture on pip install cells
  - Could benefit from a limitations section discussing when NOT to use this approach

#### Detailed Scoring

**1. Narrative Quality: 5/5**
Opens with clear problem statement about reducing support ticket volume. Each section builds logically. Concludes with discussion of production considerations.

**2. Code Quality: 4/5**
Excellent structure and naming. Clean, idiomatic code. Model defined as constant. Minor issue: pip install output not suppressed in cells 1-2.

**3. Technical Accuracy: 5/5**
Demonstrates best practices for tool use. Appropriate model selection (using valid claude-sonnet-4-5 model). Correct API usage with streaming.

**4. Actionability & Understanding: 4/5**
Very practical with clear adaptation points. Explains why tool schemas are designed certain ways. Could add more discussion on when this approach isn't suitable.

#### Specific Recommendations
1. Add `%%capture` to cells 1-2 to suppress pip install logs
2. Add "Limitations & Considerations" section discussing scenarios where simpler approaches might be better
3. Consider adding a "Variations" section showing how to adapt for different support scenarios

---

### Example 2: Needs Improvement Notebook Audit (Score: 11/20)

**Notebook**: "Text Classification with Claude"

#### Executive Summary
- **Overall Score**: 11/20
- **Key Strengths**:
  - Working code that demonstrates basic classification
  - Covers multiple classification approaches
- **Critical Issues**:
  - No introduction explaining use case or prerequisites
  - Code blocks lack explanatory text
  - No discussion of why approaches work or when to use them
  - Missing error handling and best practices

#### Detailed Scoring

**1. Narrative Quality: 2/5**
Jumps directly into code without context. No introduction explaining what problem this solves or who it's for. Sections lack connecting narrative.

**2. Code Quality: 3/5**
Code is functional but lacks structure. Variable names like `x1`, `result`, `temp` are unclear. No comments explaining non-obvious choices. Model not defined as constant at top.

**3. Technical Accuracy: 3/5**
API calls work but use invalid or deprecated model names. Model selection not explained. No discussion of token efficiency or performance.

**4. Actionability & Understanding: 3/5**
Shows multiple approaches but doesn't explain when to use each. No discussion of trade-offs. Unclear how to adapt to different classification tasks.

#### Specific Recommendations

**High Priority:**
1. Add introduction section (1-2 paragraphs) explaining:
   - What classification problems this addresses
   - Prerequisites (basic Python, API key, familiarity with classification)
   - What readers will accomplish

2. Add explanatory text before EVERY code block explaining what it does and why

3. Update to current API patterns and explain model selection rationale

**Medium Priority:**
4. Improve variable names: `x1` → `sample_text`, `result` → `classification_result`
5. Define model as constant at top: `MODEL = 'claude-sonnet-4-5'`
6. Update to use valid model names (claude-sonnet-4-5, claude-haiku-4-5, or claude-opus-4-1)
7. Add "When to Use This" section explaining which approach for which scenario

**Low Priority:**
8. Add conclusion summarizing trade-offs between approaches
9. Add "Limitations" section discussing accuracy considerations
10. Consider adding evaluation metrics example
