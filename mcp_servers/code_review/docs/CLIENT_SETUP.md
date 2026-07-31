# MCP Client Setup

The examples in `configs/` are templates. First copy `.env.example` to the
ignored local `.env` and set the API key there. Then replace
`<ABSOLUTE_PATH_TO_REPOSITORY>` in the client configuration. Never commit a
real `HY3_API_KEY`.

The Windows examples use `py -3.13 -m uv` because this development machine has
uv installed as a Python user package but its Scripts directory is not on
`PATH`. If `uv` is on `PATH`, the server command may instead be `uv` with args
starting at `--directory`. The Codex example also sets uv's cache to the
project-local ignored `.uv-cache` directory so sandboxed clients do not need
write access to the user-level uv cache.

## WorkBuddy

WorkBuddy supports project-level MCP configuration at:

```text
<repository>/.workbuddy/mcp.json
```

Setup:

1. Copy `configs/workbuddy.mcp.example.json` to
   `<repository>/.workbuddy/mcp.json`.
2. Replace `<ABSOLUTE_PATH_TO_REPOSITORY>`.
3. Confirm the ignored local `.env` contains `HY3_API_KEY`.
4. In WorkBuddy, open the MCP configuration view and confirm that
   `hy3-code-review` is green.
5. Start a new conversation and ask WorkBuddy to list the tools provided by
   `hy3-code-review`.

WorkBuddy 5.3.5 fallback observed during validation: if the project-level file
is not discovered, open **Connectors -> Custom Connector -> Configure MCP** and
paste the same server entry into the user-level configuration shown by the UI:

```text
~/.workbuddy/mcp.json
```

Save it, trust the local server once, and start a new conversation so the tool
list is refreshed. The project-level example remains the recommended portable
configuration for submission.

Suggested verification prompt:

```text
Use the hy3-code-review MCP server to review the following unified diff.
Report only evidence-backed findings and include file locations.

<paste examples/sample_bug.diff here>
```

## Codex

Codex desktop, CLI, and IDE clients share MCP configuration. For a trusted
project, use:

```text
<repository>/.codex/config.toml
```

Setup:

1. Copy `configs/codex.config.example.toml` to
   `<repository>/.codex/config.toml`.
2. Replace `<ABSOLUTE_PATH_TO_REPOSITORY>`.
3. Confirm the ignored local `.env` contains `HY3_API_KEY`.
4. Trust the project when Codex asks, then restart Codex or open a new task.
5. Confirm that `hy3-code-review` exposes all three tools. From the CLI, use
   `codex mcp list` as an additional configuration check.

Suggested verification prompt:

```text
Use generate_test_plan from the hy3-code-review MCP server for this diff.
Assume pytest and prioritize regressions and boundary conditions.

<paste examples/sample_feature.diff here>
```

## Optional Cursor compatibility

Cursor remains supported but is not required for this submission. Copy
`configs/cursor.mcp.example.json` to `<repository>/.cursor/mcp.json`, replace
the absolute path, confirm `.env` is configured, then restart the MCP server.

## Expected tools

- `review_diff`
- `explain_changes`
- `generate_test_plan`

## Troubleshooting

- Red or disconnected server: verify the absolute path and the `py` command.
- Codex reports `MCP error -32000: Connection closed`: confirm its command
  includes `--cache-dir <repository>/mcp_servers/code_review/.uv-cache` before
  `--directory`, then restart Codex or open a new task.
- Server starts but tool calls fail: verify `HY3_API_KEY`, `HY3_BASE_URL`, and
  `HY3_MODEL`.
- JSON-RPC or parsing errors: ensure the server writes no normal logs to
  stdout.
- Tools do not appear after editing config: restart the MCP server and open a
  fresh chat.
- WorkBuddy says the server is not configured: use the user-level fallback
  above, accept the one-time local-server trust prompt, then start a new task.
