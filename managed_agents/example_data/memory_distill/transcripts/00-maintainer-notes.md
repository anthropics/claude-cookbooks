# Notes from the tidewick maintainers' channel (pasted by hand)

Not a transcript: a developer copied these out of a team chat so the memory would have them.

- 2026-01-14: Agreed that Python 3.11 stays the minimum version until at least the end of 2026. Pattern
  matching is fine to use; nothing from 3.12 yet.
- 2026-01-14: No third-party dependencies, ever, including in tests. Someone asked about pytest; answer was
  no, unittest only (this is decision record 0001).
- 2026-02-02: Station ids are lowercase kebab-case and double as file names. A request to allow underscores
  was declined.
- 2026-02-11: The 0.x text data format is retired. legacy_parser.py stays only until the two remaining 0.x
  files held by a downstream user are converted; then it gets deleted. Nobody should add callers.
- 2026-02-20: Times in station files are local standard time year-round. We will not add daylight-saving
  handling to the library; a printed table that shows daylight time will differ by an hour in summer and
  that is expected. If this keeps confusing people, the fix is a sentence in the README, not code.
- 2026-03-03: Releases are cut by hand: changelog entry, bump __version__, tag vX.Y.Z. There is no CI
  publish step yet; "set up publishing" is an open item with no owner.
- Open question (no decision): whether predictions should carry the station's datum in their output. Leaning
  yes.
