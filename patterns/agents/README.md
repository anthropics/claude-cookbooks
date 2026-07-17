# Building Effective Agents Cookbook

Reference implementation for [Building Effective Agents](https://anthropic.com/research/building-effective-agents) by Erik Schluntz and Barry Zhang.

This repository contains example minimal implementations of common agent workflows discussed in the blog:

- Basic Building Blocks
  - Prompt Chaining
  - Routing
  - Multi-LLM Parallelization
- Advanced Workflows
  - Orchestrator-Subagents
  - Evaluator-Optimizer

## Getting Started
See the Jupyter notebooks for detailed examples:

- [Basic Workflows](basic_workflows.ipynb)
- [Evaluator-Optimizer Workflow](evaluator_optimizer.ipynb) 
- [Orchestrator-Workers Workflow](orchestrator_workers.ipynb)
- [Async Multi-Agent Orchestration](async_multi_agent_orchestration.ipynb)
- [Pipeline vs Barrier](pipeline_vs_barrier.ipynb) — composing sub-agents without wasting parallelism: per-item flow by default, a barrier only where a stage needs every previous result, and failure handling that drops one item instead of the whole batch
