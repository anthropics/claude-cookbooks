# Structured context compaction for long agent runs

Long-running agents accumulate verbose scratchpad state until it crowds the context window. This guide shows a three-step recipe: COMPACT prose into a dense keyed record, FORGET stale low-value facts on a deterministic decay rule, and MEASURE the token reduction offline with a local tokenizer.

The core result reproduces with no API key. On the sample scratchpad it cuts 1452 tokens to 133, a 91% reduction, while preserving 7 of 7 probe answers.

Open `guide.ipynb` to run it.
