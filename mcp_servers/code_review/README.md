# Hy3 Code Review MCP

A local `stdio` MCP server that exposes Hy3-powered code-review tools.

The server accepts unified diffs as untrusted data, calls an OpenAI-compatible
Hy3 API for reasoning, and validates the response against structured schemas
before returning it to the MCP client.

## Tools

### `review_diff`

Finds actionable defects and risks in a diff. Findings include severity,
location, evidence, and remediation.

### `explain_changes`

Explains the purpose, behavior changes, affected areas, risks, and reviewer
focus for a diff.

### `generate_test_plan`

Produces prioritized test cases for the behavior changed by a diff.

## Requirements

- Python 3.10-3.13; Python 3.12 is selected by `.python-version`
- [uv](https://docs.astral.sh/uv/)
- Node.js and `npx`, for MCP Inspector
- Access to an OpenAI-compatible Hy3 API

## Install

From this directory:

```powershell
uv sync
```

One-command tool installation is also supported:

```powershell
uv tool install .
```

On this Windows development machine, `uv` was installed as a Python user
package and its Scripts directory is not currently on `PATH`. The equivalent
command is:

```powershell
py -3.13 -m uv sync
```

## Configure

Copy `.env.example` to `.env`, then set at least:

```text
HY3_API_KEY=<your-key>
HY3_BASE_URL=https://tokenhub.tencentmaas.com/v1
HY3_MODEL=hy3
```

Never commit `.env` or a real API key.

Optional settings:

| Variable | Default | Purpose |
|---|---:|---|
| `HY3_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `HY3_MAX_RETRIES` | `2` | Retries for network, rate-limit, and 5xx errors |
| `HY3_REASONING_EFFORT` | `high` | `no_think`, `low`, or `high` |
| `HY3_MAX_INPUT_CHARS` | `60000` | Maximum diff size |
| `HY3_MAX_OUTPUT_TOKENS` | `8000` | Maximum completion size |

## Run the server

```powershell
uv run --env-file .env hy3-code-review-mcp
```

The server uses `stdio`, so a quiet terminal with no visible output is expected.
Do not add ordinary logging or `print()` calls to stdout.

## Run tests and lint

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Verify with MCP Inspector

List the tools with this tested Windows command from the project directory:

```powershell
npx -y @modelcontextprotocol/inspector@0.21.2 --cli `
  py -3.13 -m uv --directory . run hy3-code-review-mcp `
  --method tools/list
```

Call a Hy3-backed tool after setting `HY3_API_KEY` in the current shell:

```powershell
npx -y @modelcontextprotocol/inspector@0.21.2 --cli `
  -e HY3_API_KEY=$env:HY3_API_KEY `
  py -3.13 -m uv --directory . run hy3-code-review-mcp `
  --method tools/call `
  --tool-name review_diff `
  --tool-arg "diff=diff --git a/app.py b/app.py"
```

Expected result: the tool list contains `review_diff`, `explain_changes`, and
`generate_test_plan`. A tool call additionally requires a valid Hy3 API key.

When the `uv` executable is available on `PATH`, replace
`py -3.13 -m uv` with `uv`.

## Current validation status

- Python and uv project structure: complete
- MCP `stdio` server: complete
- three structured Hy3-backed tools: complete
- unit tests with mocked Hy3 responses: complete
- MCP Inspector tool discovery: complete
- one-command package installation: complete
- WorkBuddy and Codex configuration examples: complete
- live calls to all three tools through Hy3 and MCP stdio: complete
- live WorkBuddy call: complete
- live Codex call: pending interactive validation

See [docs/CLIENT_SETUP.md](docs/CLIENT_SETUP.md) for project-level client
configuration and verification prompts.

## Examples and documentation

- `examples/sample_bug.diff`: fixed input for the WorkBuddy review demo
- `examples/sample_feature.diff`: fixed input for the Codex test-plan demo
- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Client setup](docs/CLIENT_SETUP.md)
- [Demo script](docs/DEMO.md)
- [Validation evidence](docs/VALIDATION.md)
- [Upstream PR integration](docs/UPSTREAM_INTEGRATION.md)
- [中文说明](README_CN.md)

## Security summary

- Diffs are serialized as untrusted JSON data.
- The server does not read files, run Git, execute a shell, or execute reviewed code.
- API keys are read only from environment variables.
- stdout is reserved for MCP protocol messages.
- Inputs are bounded before an API request.
- Model output must pass JSON extraction and Pydantic schema validation.
- Authentication errors are not retried; transient failures use bounded retries.

## Delivery status

All local engineering, packaging, and live Hy3 API checks are complete.
WorkBuddy validation is complete. Codex end-to-end validation and the final
recording remain pending.
See [docs/VALIDATION.md](docs/VALIDATION.md) for the exact evidence and
remaining checkboxes.
