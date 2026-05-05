# Gate, expense approver

A `policy.yaml` and twelve receipts (`inbox/receipts.jsonl`) used by `CMA_gate_human_in_the_loop.py`. The agent classifies each receipt against the policy with two custom tools: `decide()` for clear approves and rejects, `escalate()` for anything ambiguous.

The twelve receipts are designed to hit every branch of the policy: a handful that should auto-approve cleanly, one with no receipt image where the policy demands one, a couple in the manager-approval band, two over the threshold, one travel charge that always escalates regardless of amount, and one with a deliberately ambiguous category. A healthy run produces a mix of `approve`, `reject`, and `escalated` decisions, never all of one lane.
