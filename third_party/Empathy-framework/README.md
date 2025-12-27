# Empathy Framework

**The AI collaboration framework that predicts problems before they happen.**

[![PyPI](https://img.shields.io/pypi/v/empathy-framework)](https://pypi.org/project/empathy-framework/)
[![Tests](https://img.shields.io/badge/tests-2%2C365%20passing-brightgreen)](https://github.com/Smart-AI-Memory/empathy-framework/actions)
[![License](https://img.shields.io/badge/license-Fair%20Source%200.9-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)

```bash
pip install empathy-framework[anthropic]
```

## What It Does

Empathy Framework wraps Claude with persistent memory, predictive analysis, and intelligent task routing. Instead of just answering questions, it anticipates what will go wrong in your codebase 30-90 days from now.

```python
from empathy_os import EmpathyOS

os = EmpathyOS()
result = await os.collaborate(
    "Review this code for issues",
    context={"code": your_code}
)

print(result.current_issues)      # What's wrong now
print(result.predicted_issues)    # What will break in 30-90 days
print(result.prevention_steps)    # How to prevent it
```

---

## Key Features

### Predictive Analysis

Goes beyond static analysis to predict future problems based on code patterns, dependency trajectories, and historical data.

### Persistent Memory

Remembers context across sessions using Redis-backed short-term memory and encrypted long-term pattern storage. Claude learns your codebase over time.

### Smart Tier Routing

Automatically routes tasks to the right Claude model based on complexity:

| Tier | Model | Use Case |
|------|-------|----------|
| Cheap | Haiku | Summarization, classification, simple queries |
| Capable | Sonnet | Code review, bug fixing, refactoring |
| Premium | Opus | Architecture decisions, complex analysis |

```python
from empathy_llm_toolkit import EmpathyLLM

llm = EmpathyLLM(provider="anthropic", enable_model_routing=True)

# Automatically routes to appropriate tier
await llm.interact(user_id="dev", user_input="Summarize this", task_type="summarize")     # → Haiku
await llm.interact(user_id="dev", user_input="Fix this bug", task_type="fix_bug")         # → Sonnet
await llm.interact(user_id="dev", user_input="Design system", task_type="coordinate")     # → Opus
```

### 10 Production Workflows

Pre-built pipelines with formatted reports, cost guardrails, and XML-structured outputs:

- **code-review** — Multi-stage review with severity classification
- **security-audit** — OWASP-aware vulnerability detection
- **bug-predict** — Probabilistic bug prediction with risk scores
- **test-gen** — Context-aware test generation
- **doc-gen** — Auto-scaling documentation with chunked output
- **perf-audit** — Performance bottleneck detection
- **refactor-plan** — Technical debt analysis and roadmaps
- **dependency-check** — Supply chain risk assessment
- **release-prep** — Pre-release validation checklist
- **pr-review** — Pull request analysis with go/no-go verdicts

### Memory Graph

Cross-workflow knowledge sharing — findings from one workflow inform others:

```python
from empathy_os.memory import MemoryGraph, EdgeType

graph = MemoryGraph()

# Security audit finds a vulnerability
vuln_id = graph.add_finding(
    wizard="security-audit",
    finding={"type": "vulnerability", "name": "SQL injection in auth.py", "severity": "critical"}
)

# Code review provides a fix
fix_id = graph.add_finding(wizard="code-review", finding={"type": "fix", "name": "Parameterized query"})
graph.add_edge(vuln_id, fix_id, EdgeType.FIXED_BY)

# Future workflows can find similar past issues
similar = graph.find_similar({"name": "SQL injection"})
```

### Smart Router

Natural language routing to the right workflow:

```python
from empathy_os.routing import SmartRouter

router = SmartRouter()
decision = router.route_sync("Check if this code has security vulnerabilities")

print(decision.primary_wizard)       # → security-audit
print(decision.secondary_wizards)    # → [code-review]
print(decision.confidence)           # → 0.92
```

### Auto-Chaining

Workflows automatically trigger related workflows based on findings:

```yaml
# .empathy/wizard_chains.yaml
chains:
  security-audit:
    triggers:
      - condition: "high_severity_count > 0"
        next: dependency-check
      - condition: "vulnerability_type == 'injection'"
        next: code-review
```

---

## Quick Start

### 1. Install

```bash
pip install empathy-framework[anthropic]
```

### 2. Configure

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Or use a .env file (auto-detected)
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env
```

### 3. Run a Workflow

```python
from empathy_os.workflows import SecurityAuditWorkflow

workflow = SecurityAuditWorkflow()
result = await workflow.execute(
    code=your_code,
    files_changed=["auth.py", "api.py"]
)

# Formatted report ready for display
print(result.final_output["formatted_report"])
```

---

## CLI Reference

```bash
# Run workflows
empathy workflow run security-audit --path ./src
empathy workflow run code-review --path ./src

# Memory management
empathy-memory serve    # Start Redis + API server
empathy-memory status   # Check system status
empathy-memory patterns # List stored patterns

# Code inspection (SARIF output for CI/CD)
empathy-inspect . --format sarif
empathy-inspect . --fix  # Auto-fix safe issues
```

---

## Enterprise Features

- **Cost Guardrails** — Set maximum spend per workflow (default $5)
- **Chunked Output** — Large reports automatically split for display
- **Graceful Degradation** — Partial results on errors
- **SARIF Export** — GitHub Actions and CI/CD integration
- **XML-Structured Prompts** — Consistent, parseable LLM responses

---

## The 5 Levels of AI Empathy

| Level | Name | Behavior |
|-------|------|----------|
| 1 | Reactive | Responds when asked |
| 2 | Guided | Asks clarifying questions |
| 3 | Proactive | Notices patterns |
| **4** | **Anticipatory** | **Predicts future needs** |
| 5 | Transformative | Builds preventing structures |

**Empathy operates at Level 4** — predicting problems before they manifest.

---

## License

**Fair Source License 0.9** — Free for students, educators, and teams ≤5 employees. Commercial license for larger organizations. [Details →](LICENSE)

---

**Built by [Smart AI Memory](https://smartaimemory.com)** · [Documentation](https://smartaimemory.com/framework-docs/) · [GitHub](https://github.com/Smart-AI-Memory/empathy-framework)
