# What is in sweep.jsonl

Every line ran with prompt caching on (its caching field says "on").

15,172 task attempts count, of 15,246 run, in 3 rounds and 33 settings.

The file is about 8.4 MB.

Left out, by rule:

- cold cache on the first request: 67
- a request was tried again: 7

## What is in baseline.jsonl

No request behind these lines carried cache_control (their caching field says "off").

462 task attempts count, of 462 run, in 3 rounds and 1 setting.

Left out, by rule: none

## Fields in both files

Each line is one task attempt. The fields that latency_stats.py's Sweep reads are: round; the six Config fields (model, effort, thinking, speed, loop, commentary) and caching ("on" in sweep.jsonl, "off" in baseline.jsonl), which the notebook's [Prompt caching](../latency_optimization.ipynb#prompt-caching) section uses to compare the baseline with and without caching; task, type, level, and cluster (a task's id, its job, its level, and the group of tasks redrawn together, which is the task's own id when tasks are independent); correct; secs; the four token counts priced in PRICE (input_tokens, cache_write, cache_read, output_tokens); and call_secs, call_first_token_secs, call_output_tokens, and call_thinking_tokens, with one entry per model call. secs and call_secs are the service's own timing of each request, less a step that only our test harness adds, plus a fixed 0.13 seconds a call to stand for the network. call_first_token_secs is each model call's first-token seconds: the service's own time to its first generated token (thinking included), plus the same fixed 0.13 seconds. Like call_secs, it is the service's own timing. When a call thinks before it writes, its first token is a thinking token, so nothing readable reaches the client at that moment; the notebook estimates a task's first visible token by adding the first call's thinking at that call's own rate of output. call_thinking_tokens is the part of each call's output tokens that was thinking.

## What is in race.jsonl

The final run behind the notebook's [Putting it all together](../latency_optimization.ipynb#putting-it-all-together) section: 9 shortlisted model settings (Haiku 5.5 and Sonnet 5.5 at every effort, Opus 5.5 with fast mode at every effort), each with prefetch and bigger pages on or off.

16,632 task attempts count, of 16,632 run, in 3 rounds and 36 settings. The notebook leaves out Haiku 5.5 at `low`, which fell short of its 95% bar on the baseline loop, and ranks the other 32. Every line ran with prompt caching on, and each setting's cache was written before its tasks started, so no counted attempt found it cold.

The run had no time limit, and 49 attempts ran past the notebook's 60-second `TIME_LIMIT`, all on Haiku 5.5 at `high`. The file keeps them as they ran. The notebook reads it with `stop=TIME_LIMIT`, which scores each one as `run_task()` would have left it: stopped at 60 seconds, with nothing recorded, so wrong.

The fields are those of sweep.jsonl, plus call_first_visible_secs, each model call's seconds to its first text or tool call, measured directly, and first_cache_read, the first call's cache read. Seconds in this file are timed by the client that ran the loop, from the start of each request to its last event, so they include the network.
