# Architecture

## Purpose

Hy3 Code Review MCP is a local `stdio` MCP server. It turns three focused
code-review operations into tools that WorkBuddy, Codex, CodeBuddy, and other
MCP hosts can discover and call.

## Data flow

```text
MCP host
  |
  | JSON-RPC over stdio
  v
FastMCP tool handler
  |
  | validated parameters
  v
CodeReviewService
  |-- input bounds
  |-- untrusted-data serialization
  |-- tool-specific prompt contract
  v
Hy3Client
  |
  | OpenAI-compatible HTTPS request
  v
Hy3 API
  |
  | model text
  v
JSON extraction + Pydantic validation
  |
  | structured MCP result
  v
MCP host
```

## Components

| Component | Responsibility |
|---|---|
| `server.py` | MCP registration, tool descriptions, stdio entry point |
| `config.py` | Environment loading and validation |
| `hy3_client.py` | Hy3 request construction, timeout, retry, error normalization |
| `service.py` | Input validation, prompts, result filtering |
| `prompts.py` | Tool-specific output and security contracts |
| `parsing.py` | JSON extraction and schema validation |
| `schemas.py` | Stable structured output models |

## Tool boundaries

### `review_diff`

- Receives a unified diff and optional review context.
- Calls Hy3 once.
- Validates a `ReviewResult`.
- Enforces the requested severity threshold.

### `explain_changes`

- Receives a unified diff and intended audience.
- Calls Hy3 once.
- Validates a `ChangeExplanation`.
- Removes risks when `include_risks=false`.

### `generate_test_plan`

- Receives a unified diff, test framework, and optional test context.
- Calls Hy3 once.
- Validates a prioritized `TestPlan`.

## Trust boundaries

### Untrusted diff content

Diffs may contain comments or strings that resemble instructions. They are
serialized inside a JSON payload and the system prompt explicitly defines all
payload fields as untrusted data. The server does not execute code from a diff.

### Secrets

The API key is loaded only from `HY3_API_KEY`. It is not logged, returned in
errors, placed in prompts, or stored by the server.

### Local machine

The current tools do not read arbitrary files, run Git, invoke a shell, or
write to the repository. The MCP client must supply the diff.

### Model output

Model output is not trusted as structured data until it has passed JSON
extraction and Pydantic validation. Invalid output produces a tool error
instead of a fabricated partial result.

## Failure behavior

| Failure | Behavior |
|---|---|
| Missing API key | Clear tool error; discovery still works |
| Empty or oversized diff | Rejected before an API call |
| Rate limit/timeout/network error | Bounded retry with backoff |
| Authentication/other 4xx | No retry; normalized error |
| API 5xx | Bounded retry |
| Empty or malformed model output | Structured response error |
| Normal server startup | No stdout logging; stdio remains protocol-only |

## Non-goals

- Reading a repository automatically
- Running builds, tests, or arbitrary code
- Posting GitHub review comments
- Training or locally serving Hy3
- Public HTTP deployment
