# Future AGI <> Claude Cookbooks

[Future AGI](https://futureagi.com) is an observability and evaluation platform for AI agents and LLM applications. The [`traceAI`](https://github.com/future-agi/traceAI) open-source library auto-instruments the Anthropic Python SDK (and many other frameworks) with OpenTelemetry, so every `client.messages.create(...)` call shows up as a fully-attributed span in your Future AGI project with no manual tracing code.

Here we provide a cookbook for wiring Future AGI tracing into Claude API calls.

1. [`future_agi_observability.ipynb`](./future_agi_observability.ipynb) — quick-start showing how to register the Future AGI tracer, instrument the Anthropic SDK, and inspect the resulting span (model, input messages, tool_use response, token usage) in the Future AGI dashboard.

# More about Future AGI

- [Documentation](https://docs.futureagi.com)
- [traceAI on GitHub](https://github.com/future-agi/traceAI)
- [traceAI-anthropic on PyPI](https://pypi.org/project/traceAI-anthropic/)
- [Dashboard](https://app.futureagi.com)

# Get Started

If you're ready to start tracing your Claude apps with Future AGI, head over to [app.futureagi.com](https://app.futureagi.com) to grab your free `FI_API_KEY` and `FI_SECRET_KEY`, then open the notebook above.
