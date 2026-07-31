# Validation Record

Date: 2026-07-31
Platform: Windows, PowerShell
Project Python: CPython 3.12.13 managed by uv

## Automated checks

| Check | Result |
|---|---|
| Unit and service tests | 20 passed |
| stdio + fake Hy3 API end-to-end test | 1 passed |
| Ruff lint | Passed |
| Ruff format check | Passed |
| Wheel build | Passed |
| Source distribution build | Passed |
| Apache-2.0 license included in wheel | Passed |
| Config JSON parsing | Passed |
| Secret-pattern scan | Passed |

The stdio integration test initializes a real subprocess, lists the three
tools, verifies an invalid tool call, starts a local OpenAI-compatible fake Hy3
endpoint, calls `review_diff`, and checks the structured MCP result. This covers
the complete client -> stdio -> server -> HTTP API -> parser -> client path
without sending external traffic. On the managed test runner, Windows named
pipes require local-machine permissions; the same test passed when run with
those permissions.

## MCP Inspector

Verified with `@modelcontextprotocol/inspector@0.21.2`:

- `tools/list` through the uv development command: passed.
- `tools/list` through the executable created by `uv tool install .`: passed.
- Missing-key tool call returns `isError: true` with a clear message: passed.

Discovered tools:

```text
review_diff
explain_changes
generate_test_plan
```

## Package inspection

Built artifacts:

```text
dist/hy3_code_review_mcp-0.1.0-py3-none-any.whl
dist/hy3_code_review_mcp-0.1.0.tar.gz
```

Archive inspection confirmed that package artifacts contain source and package
metadata but do not contain `.env`, caches, tests, or local tool environments.

## Live Hy3 validation

Validated on 2026-07-28 against the TokenHub `hy3` model through a real MCP
stdio subprocess:

- [x] `review_diff`: returned one high-severity finding at
  `src/profile.py:13` for the missing `None` check.
- [x] `explain_changes`: returned the behavior change and three regression
  risks.
- [x] `generate_test_plan`: returned seven pytest scenarios, including tests
  that expose the one-based pagination offset defect.

The repeatable validation command is:

```powershell
py -3.13 -m uv run python scripts/validate_live.py
```

It reads the ignored local `.env`, never prints the API key, lists the MCP
tools, calls all three tools, and checks their structured results.

## Desktop client validation

- [x] WorkBuddy 5.3.5 end-to-end Demo A:
  - connected through the user-level `~/.workbuddy/mcp.json` fallback;
  - invoked `review_diff` with `severity_threshold=medium`;
  - returned one high-severity finding at `src/profile.py:13`;
  - identified the missing `None` check and recommended restoring the guard.

The following still require interactive validation:

- [ ] Codex end-to-end Demo B
- [ ] Video/GIF recording

These items must be completed before claiming the Issue is fully delivered.

## Reproduction commands

```powershell
py -3.13 -m uv sync
py -3.13 -m uv run pytest
py -3.13 -m uv run ruff check .
py -3.13 -m uv run ruff format --check .
py -3.13 -m uv build
```

Inspector:

```powershell
npx -y @modelcontextprotocol/inspector@0.21.2 --cli `
  py -3.13 -m uv --directory . run hy3-code-review-mcp `
  --method tools/list
```
