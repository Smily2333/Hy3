# Upstream Integration

Target repository:

```text
https://github.com/Tencent-Hunyuan/Hy3
```

Target base branch:

```text
rhinobird2026
```

## Destination

Copy this project to:

```text
mcp_servers/code_review/
```

This follows the structure used by existing Rhinobird MCP submissions under
`mcp_servers/<scenario>/`.

## Root README entry

When the current upstream README contains an MCP Applications section, add:

```markdown
- [Hy3 Code Review MCP](./mcp_servers/code_review/README.md):
  a local `stdio` MCP server for evidence-backed diff review, change
  explanation, and prioritized test planning with Hy3.
```

Add the equivalent Chinese entry to `README_CN.md` linking to
`mcp_servers/code_review/README_CN.md`.

## Pull request checklist

- [x] Fork remote is configured.
- [x] Work branch starts from `rhinobird2026`.
- [x] Only relevant project files are changed.
- [x] Test, lint, format, and build commands pass from a clean checkout.
- [x] WorkBuddy and Codex validations are recorded.
- [x] Demo videos are linked.
- [x] PR title references Issue #3.
- [x] PR base is `Tencent-Hunyuan/Hy3:rhinobird2026`.

Suggested PR title:

```text
feat(mcp): add Hy3 code review MCP server
```

Suggested PR summary:

```text
Adds a local stdio MCP server powered by the Hy3 API with three structured
tools: diff review, change explanation, and test-plan generation. Includes
one-command installation, WorkBuddy/Codex project configuration examples,
tests, security boundaries, and end-to-end demo evidence.
```
