# 建構有效代理實用指南

# Building Effective Agents Cookbook

由 Erik Schluntz 和 Barry Zhang 撰寫的[建構有效代理](https://anthropic.com/research/building-effective-agents)參考實作。

Reference implementation for [Building Effective Agents](https://anthropic.com/research/building-effective-agents) by Erik Schluntz and Barry Zhang.

> **[English version below](#english-version) | 英文版本請見下方**

本儲存庫包含部落格文章中討論的常見代理工作流程的範例最小實作：

- 基礎建構區塊
  - 提示詞鏈接（Prompt Chaining）
  - 路由（Routing）
  - 多 LLM 並行化
- 進階工作流程
  - 協調器-子代理
  - 評估器-優化器

## 開始使用
請參閱 Jupyter notebooks 以獲得詳細範例：

- [基礎工作流程](basic_workflows.ipynb)
- [評估器-優化器工作流程](evaluator_optimizer.ipynb)
- [協調器-工作者工作流程](orchestrator_workers.ipynb)

---

<a name="english-version"></a>

## English Version

This repository contains example minimal implementations of common agent workflows discussed in the blog:

- Basic Building Blocks
  - Prompt Chaining
  - Routing
  - Multi-LLM Parallelization
- Advanced Workflows
  - Orchestrator-Subagents
  - Evaluator-Optimizer

### Getting Started
See the Jupyter notebooks for detailed examples:

- [Basic Workflows](basic_workflows.ipynb)
- [Evaluator-Optimizer Workflow](evaluator_optimizer.ipynb)
- [Orchestrator-Workers Workflow](orchestrator_workers.ipynb)
