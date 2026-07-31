# Demo Plan

The final recording should be no longer than two minutes and show real calls
from two MCP clients. Do not display a real API key.

## Preflight

1. Install with `uv tool install .` or run with `uv --directory`.
2. Configure WorkBuddy and Codex using `docs/CLIENT_SETUP.md`.
3. Confirm the clients show all three tools.
4. Keep `examples/sample_bug.diff` and `examples/sample_feature.diff` open.
5. Clear terminals and UI panels that may expose secrets.

## Demo A: WorkBuddy code review

Target duration: 45-55 seconds.

Prompt:

```text
Use review_diff from the hy3-code-review MCP server.
Review this Python diff for correctness and return findings of medium severity
or higher. Do not invent issues that are not supported by the diff.

<paste examples/sample_bug.diff>
```

Expected evidence:

- WorkBuddy visibly calls `review_diff`.
- The result identifies that `repository.find(user_id)` can return `None`.
- The result points to `src/profile.py`.
- The result suggests restoring a missing-value check.

## Demo B: Codex test plan

Target duration: 45-55 seconds.

Prompt:

```text
Use generate_test_plan from the hy3-code-review MCP server.
Assume pytest. Create a prioritized test plan for this pagination change,
including boundary and regression cases.

<paste examples/sample_feature.diff>
```

Expected evidence:

- Codex visibly calls `generate_test_plan`.
- The plan covers page 1, invalid pages, page-size bounds, and empty results.
- At least one test exposes the one-based pagination offset defect.

## Optional closing shot

Show the MCP server configuration and the three available tool names:

- `review_diff`
- `explain_changes`
- `generate_test_plan`

## Recording checklist

- [ ] Both clients are visible by name.
- [ ] Both calls are real Hy3 API calls.
- [ ] Tool names are visible.
- [ ] No API key or private path is exposed.
- [ ] Results are readable at normal playback speed.
- [ ] Total duration is at most two minutes.
- [ ] GIF/video is added under `assets/` or linked from README.
