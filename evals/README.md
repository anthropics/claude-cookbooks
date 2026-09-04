# Evals

Recipes for measuring model and pipeline quality with runnable evaluation harnesses.

- [Reproduce Claude's agentic search benchmark scores](agentic_search/reproduce_agentic_search_benchmarks.ipynb) — a Messages API harness that reproduces published DeepSearchQA and BrowseComp scores.
- [Citation-faithfulness evals: catching hallucinated support](citation_faithfulness/citation_faithfulness_evals.ipynb) — a two-stage citation auditor (deterministic quote-existence gate + skeptical LLM judge) scored on a labelled trap dataset of fabricated, misattributed, and plausible-but-unsupported citations.
