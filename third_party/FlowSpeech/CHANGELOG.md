# FlowSpeech Integration Changes

## 2026-10-26 - Public API v1

- Replace the legacy synchronous base64 endpoint with asynchronous jobs and WAV downloads.
- Preserve caller-known request IDs across retries, interruptions, and recovery.
- Add strict input/result validation, identity correlation, safe credential-free downloads,
  bounded retries, Retry-After handling, and one configurable total deadline.
- Validate complete PCM WAV structure, not merely its header.
- Add offline contract and runnable-integration tests plus extracted-bundle verification.

This updates an existing integration PR, not a separately versioned package or
published release. Coordinator review and upstream acceptance remain required.
