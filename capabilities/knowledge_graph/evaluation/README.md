# Knowledge Graph Extraction Evaluation

Scores entity and relation extraction against the hand-labeled gold set in `../data/sample_triples.json`.

## Running

From the repository root, install dependencies and set your API key:

```bash
uv sync --all-extras
cp .env.example .env  # then edit .env to add ANTHROPIC_API_KEY
```

Then:

```bash
uv run python capabilities/knowledge_graph/evaluation/eval_extraction.py
```

## Metrics

**Entity P/R/F1** — an extracted entity counts as a true positive if its canonicalized name matches a gold entity in the same document. Canonicalization lowercases and maps known surface-form variants ("National Aeronautics and Space Administration" → "nasa") via `data/alias_map.json`.

**Relation P/R/F1** — a relation counts as a true positive if both canonicalized endpoints match a gold (source, target) pair. **Predicate wording is ignored**: "commanded" and "was commander of" both count, but so would a semantically wrong predicate like "destroyed" between the same two entities. This makes the reported relation recall an upper bound — it measures whether the extractor found the right *connections*, not whether it labeled them correctly. For stricter scoring you would add a predicate-similarity check (e.g. a Claude judge call per candidate pair).

## Expected baseline

With `claude-haiku-4-5` and the extraction prompt from the guide, expect roughly:

| Metric | P | R | F1 |
|---|---|---|---|
| Entities | 0.80–0.90 | 0.70–0.85 | 0.75–0.85 |
| Relations | 0.70–0.85 | 0.55–0.70 | 0.60–0.75 |

These ranges are indicative; actual scores vary run-to-run due to model non-determinism.

Recall on relations is the hard number — the extractor tends to be conservative, preferring fewer high-confidence edges over exhaustive coverage. Tuning the extraction prompt for higher recall (e.g. "extract every stated relationship, even minor ones") trades precision for recall.
