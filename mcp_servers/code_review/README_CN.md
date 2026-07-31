# Hy3 Code Review MCP

这是一个本地 `stdio` MCP Server，将 Hy3 的代码理解和推理能力封装为三个可被
WorkBuddy、Codex、CodeBuddy 等 MCP 客户端直接调用的工具。

Server 把 unified diff 视为不可信数据，调用兼容 OpenAI 协议的 Hy3 API，并在
返回客户端前使用固定 Schema 校验模型输出。

## 功能

### `review_diff`

审查 diff 中有证据支持的缺陷和风险，返回严重等级、代码位置、原因和修改建议。

### `explain_changes`

解释变更目的、行为变化、受影响模块、潜在风险和评审重点。

### `generate_test_plan`

根据 diff、测试框架和已有测试信息，生成有优先级的测试计划。

## 环境要求

- Python 3.10-3.13，项目默认使用 uv 管理的 Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Node.js 和 `npx`，用于 MCP Inspector
- 可访问兼容 OpenAI 协议的 Hy3 API

## 安装

进入本目录：

```powershell
uv sync
```

也可以一条命令安装为本地工具：

```powershell
uv tool install .
```

本机的 uv 通过 Python 用户包安装，若 `uv` 不在 PATH 中，可使用：

```powershell
py -3.13 -m uv sync
```

## 配置

复制 `.env.example` 为 `.env`，至少设置：

```text
HY3_API_KEY=<你的 Key>
HY3_BASE_URL=https://tokenhub.tencentmaas.com/v1
HY3_MODEL=hy3
```

不要提交 `.env` 或真实 API Key。

可选环境变量：

| 变量 | 默认值 | 说明 |
|---|---:|---|
| `HY3_TIMEOUT_SECONDS` | `120` | 单次 API 请求超时 |
| `HY3_MAX_RETRIES` | `2` | 网络、限流和 5xx 的最大重试次数 |
| `HY3_REASONING_EFFORT` | `high` | `no_think`、`low` 或 `high` |
| `HY3_MAX_INPUT_CHARS` | `60000` | diff 最大字符数 |
| `HY3_MAX_OUTPUT_TOKENS` | `8000` | 模型最大输出 token |

## 启动

```powershell
uv run --env-file .env hy3-code-review-mcp
```

Server 使用 stdio。启动后终端没有普通输出是正常现象；不要向 stdout 写日志。

## 测试

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

## MCP Inspector

在本目录运行：

```powershell
npx -y @modelcontextprotocol/inspector@0.21.2 --cli `
  py -3.13 -m uv --directory . run hy3-code-review-mcp `
  --method tools/list
```

应发现：

```text
review_diff
explain_changes
generate_test_plan
```

## 客户端接入

项目提供：

- `configs/workbuddy.mcp.example.json`
- `configs/codex.config.example.toml`
- `configs/cursor.mcp.example.json`（可选）

完整操作见 [docs/CLIENT_SETUP.md](docs/CLIENT_SETUP.md)。

WorkBuddy 项目级配置路径：

```text
<项目根目录>/.workbuddy/mcp.json
```

Codex 项目级配置路径：

```text
<项目根目录>/.codex/config.toml
```

只在被忽略的本地 `.env` 中填写真实 Key，不要提交带密钥的文件。

## 示例和演示

- `examples/sample_bug.diff`：用于演示 `review_diff`
- `examples/sample_feature.diff`：用于演示 `generate_test_plan`
- [Demo 脚本](docs/DEMO.md)
- [验证记录](docs/VALIDATION.md)
- [架构和安全边界](docs/ARCHITECTURE.md)

## 安全设计

- diff 作为 JSON 数据传入，不作为指令执行；
- 不读取任意本地文件，不运行 Git、Shell 或待审查代码；
- API Key 只来自环境变量；
- stdout 只用于 MCP 协议；
- 输入在调用 API 前进行长度检查；
- 模型输出经过 JSON 提取和 Pydantic Schema 校验；
- 鉴权错误不重试，网络、限流和 5xx 只进行有限重试。

## 当前状态

已经完成并验证：

- 三个 MCP tools；
- pytest、Ruff、stdio 子进程测试；
- wheel 和 sdist 构建；
- `uv tool install .` 一键安装；
- Inspector 通过开发入口和安装入口发现 tools；
- WorkBuddy 和 Codex 项目级配置示例。

真实 Hy3 验收已完成，三个 tools 均已通过 MCP stdio 调用。仍需完成：

- WorkBuddy 端到端 `review_diff` 演示已完成；
- Codex 端到端演示；
- 最终视频或 GIF。

完成这些外部验证前，不应宣称 Issue 已全部交付。
