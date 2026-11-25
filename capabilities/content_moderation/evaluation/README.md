# Evaluation

Runs the full pipeline against the labeled samples in all three domains
(`data/<domain>/samples.jsonl`) and compares each decision to its expected label.
Uses `engine.py` and `pipeline.py` from the cookbook folder, the same modules the
guide imports.

```bash
pip install anthropic python-dotenv
# from capabilities/content_moderation/ (needs ANTHROPIC_API_KEY):
python evaluation/run_eval.py
```

The ad_creatives domain uses the hand-written ruleset in `data/ad_creatives/rules.golden.json`;
the other two domains are compiled by Claude on first run and cached under
`evaluation/compiled/`. Results are written to `evaluation/results.json`.
