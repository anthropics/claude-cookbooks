# FlowSpeech v1 Migration Handoff

## Unreleased Candidate Verification (2026-10-27)

This section records the current local candidate, not a published fix. Runtime
source was not changed during this artifact/evidence refresh. The independently
reviewed source suite passed 243 tests; this refresh rebuilt a separately named
candidate and passed **243 extracted-runtime tests, zero failures**.

Candidate: `third_party/FlowSpeech/dist/unreleased-20261027-final/flowspeech-v1-cookbook-review.tar.gz`

SHA-256: `0b4d4c36348da64dd4ee14636851d060af05cd8871823720bb1a23c1c60bcdce`

Frozen `flowspeech_v1.py` SHA-256:
`32b581099c094e8829952f0cc20663921908e00cb9432bba1d5b444aa8b5354f`

The existing six-file allowlist matched the extracted archive and source byte
for byte. The credential-pattern scan passed. Current local tests (including
worker lifecycle and error privacy regressions) were run against the extracted
runtime via `FLOWSPEECH_TEST_ROOT`; tests and local verification helpers are not
included in the archive. This is source validation, not deployment validation.

### Command and Local Evidence

From the repository root, set `PY` to the existing Python 3.12.1 test interpreter
with HTTPX 0.28.1 and pytest 9.0.3:

```bash
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 "$PY" third_party/FlowSpeech/dist/verify_unreleased_20261027.py unreleased-20261027-final
```

The local-only wrapper uses the unchanged `verify_bundle.py` with a new output
path, refuses an existing candidate directory, and verifies that the previous
fixed-path archive and frozen runtime hash remain unchanged. For another run,
use a fresh directory label instead of overwriting this evidence. Its
`validation.json` is alongside the candidate. Generated helpers, archives and
evidence under `dist/` are local artifacts, not files to stage or publish.

### Historical Evidence and Limits

The 2026-10-26 section below is retained verbatim as historical evidence; its
test counts and archive hash do not describe this candidate. Before this refresh,
earlier verification had already regenerated the fixed-name archive, so the
original 26 October archive bytes are no longer present at that path. This
refresh preserves the existing fixed-name file, whose SHA-256 equals the new
candidate SHA-256 above. It does not reconstruct or claim to revalidate the
historical archive.

No API keys, paid generation, commits, pushes, publishes, or version changes
were involved. No live writing/speech generation or full Jupyter kernel run was performed.
Independent cross-review covered source, not this new archive. A blocked sync
transport can finish its one in-flight operation after caller timeout; workers
remain bounded, with no queued late submission and no caller-owned client close.

## Historical Handoff (2026-10-26)


Date: 2026-10-26. Branch: `codex/add-flowspeech-cookbook`.
Base commit: `57a678c2542856957d0c0aeac9f897b4eb610335`.
Existing PR: https://github.com/anthropics/claude-cookbooks/pull/812

## Implementation

The actual runnable notebook now imports local v1 helpers. It persists a private
request manifest before speech submission, reloads the saved script on restart,
maps labelled turns to ordered segments, downloads validated WAV, and never
overwrites an existing output. The old endpoint/base64 contract is removed.
The public docs cover API subscription requirements, recovery, deadlines,
unsupported options, and offline checks. No underlying speech-engine names were
added. This integration has no independent package version to bump.

All HTTP tests use httpx.MockTransport; an autouse fixture rejects real socket
connections. No production key or paid generation was used. A pinned Ruff 0.14.2
binary wheel was installed under the owned cookbook directory, without source
build hooks. The existing Python test environment was used read-only with bytecode
writes disabled. No commits, pushes, publishes, or upstream PR edits were made.

The clones preserve the requested branches. Git 2.26.2 initially left partial
checkouts; system Git 2.39.3 completed and repaired only files from these newly
created clones before implementation. Both repositories were clean at that point.
No AGENTS.md exists in either checked-out Git tree. Cookbook CONTRIBUTING.md and
CLAUDE.md, plus the podcast README contribution section, were read.

The two adapter copies have identical Python ASTs (formatting follows each repo).
Both enforce stable caller-known UUIDs, strict input/result validation, normalized
identity correlation, pending/terminal/deleted states, read-only recovery, bounded
credential-free downloads, complete PCM WAV checks, and a total deadline. Retry-
After survives body-read failures; status retries wait at least five seconds;
explicit nonretryable API errors do not replay. Timeout workers may complete one
in-flight HTTP operation but cannot perform another request or paid submission.
No code automatically cancels a paid job.

## Exact Checks

Local Python 3.12.14, httpx 0.28.1, pytest 8.4.2, Ruff 0.14.2.
Run from the repository root, with
`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`:

- `python -m pytest third_party/FlowSpeech/tests --confcutdir=third_party/FlowSpeech/tests -p no:cacheprovider --basetemp=third_party/FlowSpeech/.test-tmp -q`:
  213 passed, 0 failed.
- `python third_party/FlowSpeech/verify_bundle.py`: 213 passed, 0 failed against
  the extracted runtime and notebook. Six exact allowlisted files match source;
  secret-pattern scan passed.
- `ruff check third_party/FlowSpeech`: passed.
- `ruff format --check third_party/FlowSpeech`: 10 files passed.
- `python scripts/validate_notebooks.py third_party/FlowSpeech/claude_directed_narration.ipynb`:
  one notebook passed.
- `git diff --check`: passed.
- Legacy endpoint, audioBase64, and originalText search in this integration:
  no matches.

The extracted notebook code executes twice against mocked writing and speech
clients: one initial writing request and one speech submission total, followed
by credential-free download; the second run uses the saved script and WAV.
Tests also cover output races, private file modes, missing/malformed metadata,
UUID casing/mismatches, slow requests/streams, cooldowns, and WAV truncation.

## Artifact

`third_party/FlowSpeech/dist/flowspeech-v1-cookbook-review.tar.gz`

SHA-256:
`73014ba3207174480bf107e9bbb74ce492b231591e2c6c0530fe92dbdee9a144`.
Review-only bundle, not a separately installable or published package.

## Changed Files

- `.github/workflows/flowspeech-offline.yml`.
- Under `third_party/FlowSpeech/`: `README.md`, `requirements.txt`,
  `claude_directed_narration.ipynb`, `.gitignore`, `CHANGELOG.md`,
  `flowspeech_v1.py`, `flowspeech_notebook.py`, `verify_bundle.py`, this report.
- Under `third_party/FlowSpeech/tests/`: `conftest.py`,
  `test_v1_contract.py`, `test_job_identifiers.py`, `test_wav_validation.py`,
  `test_hardening.py`, `test_notebook.py`.

## Coordinator Next Steps

Review the diff and update the existing branch/PR only. Include the adjacent
helper modules with the notebook. The new offline CI matrix targets Python
3.11 and 3.12; it has not run remotely and only 3.12 was tested locally.
No live writing/speech generation or full Jupyter kernel execution was performed;
actual notebook code cells were extracted, compiled, and executed with mocks.
No implementation blocker remains from the scoped migration.
