# Demo Assistant MCP Server

[![CI](https://github.com/grimlor/demo-assistant-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/grimlor/demo-assistant-mcp/actions/workflows/ci.yml)
[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/grimlor/49d45255ee72d31c0213cf11887a7f71/raw/demo-assistant-coverage-badge.json)](https://github.com/grimlor/demo-assistant-mcp/actions/workflows/ci.yml)

An MCP server for orchestrating demo script execution with GitHub Copilot. Enables presenters to step through demo prompts with confirmation and variable substitution.

## Quick Install

[<img src="https://img.shields.io/badge/VS_Code-VS_Code?style=flat-square&label=Install%20Server&color=0098FF" alt="Install in VS Code">](https://vscode.dev/redirect?url=vscode%3Amcp/install%3F%257B%2522name%2522%253A%2520%2522demo-assistant-mcp%2522%252C%2520%2522command%2522%253A%2520%2522uvx%2522%252C%2520%2522args%2522%253A%2520%255B%2522--from%2522%252C%2520%2522git%252Bhttps%253A//github.com/grimlor/demo-assistant-mcp%2522%252C%2520%2522demo-assistant-mcp%2522%255D%252C%2520%2522type%2522%253A%2520%2522stdio%2522%257D) [<img alt="Install in VS Code Insiders" src="https://img.shields.io/badge/VS_Code_Insiders-VS_Code_Insiders?style=flat-square&label=Install%20Server&color=24bfa5">](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp/install%3F%257B%2522name%2522%253A%2520%2522demo-assistant-mcp%2522%252C%2520%2522command%2522%253A%2520%2522uvx%2522%252C%2520%2522args%2522%253A%2520%255B%2522--from%2522%252C%2520%2522git%252Bhttps%253A//github.com/grimlor/demo-assistant-mcp%2522%252C%2520%2522demo-assistant-mcp%2522%255D%252C%2520%2522type%2522%253A%2520%2522stdio%2522%257D)

*Click a badge above to install with one click, or follow manual installation below.*

## Features

- **Sequential Execution**: Step through prompts one at a time with confirmation
- **Variable Substitution**: Dynamic values like `[PR_ID]` or `[BRANCH_NAME]`
- **State Management**: Track progress, reset, query status
- **Error Handling**: Actionable errors with suggestions via [actionable-errors](https://github.com/grimlor/actionable-errors)
- **Format Validation**: Strict parsing with helpful error messages

## Demo Script Format

Create markdown files with tagged prompts:

````markdown
### 💬 COPILOT CHAT PROMPT:
```
What Azure DevOps repository am I working in?
```

### 💬 COPILOT CHAT PROMPT:
```
Analyze PR [PR_ID] and show me the comments
```
````

Variables in `[BRACKETS]` are detected and can be substituted at execution time.

## Usage

In Copilot Chat:

```
You: Load my demo script at /path/to/demo.md

Copilot: [Loads and parses, shows first prompt]

You: confirm

Copilot: [Executes prompt, shows next one]

You: Execute with PR ID 12345

Copilot: [Substitutes variable and executes]
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `load_demo_script` | Load and parse a demo markdown file |
| `next_demo_step` | Present next prompt for review |
| `execute_demo_step` | Execute current/modified prompt |
| `reset_demo` | Reset to beginning |
| `get_demo_state` | Query current progress |

## Installation

### Quick Install (Recommended)

Click one of the badges at the top to automatically install in VS Code!

### Manual Installation

```bash
cd demo-assistant-mcp
uv sync --all-extras
```

## VS Code / Copilot Configuration

Add to your VS Code settings or `.vscode/mcp.json`:

```json
{
  "mcp.servers": {
    "demo-assistant": {
      "command": "uv",
      "args": ["run", "demo-assistant-mcp"],
      "cwd": "/path/to/demo-assistant-mcp",
      "description": "Orchestrate demo script execution"
    }
  }
}
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed setup instructions including Windows/WSL.

## Development

```bash
uv run task check                # lint + type + test (all-in-one)
uv run task test                 # Run tests (25 BDD specs)
uv run task cov                  # Run tests with coverage
uv run task lint                 # Lint (with auto-fix)
uv run task format               # Format code
uv run task type                 # Type check
```

> **Note:** `uv run` is optional when the venv is activated via direnv.

### Project Structure

```
src/demo_assistant_mcp/
├── server.py              # FastMCP server entry point
├── tools/
│   └── demo_tools.py      # Tool implementations
└── common/
    ├── demo_parser.py     # Markdown parsing
    ├── demo_state.py      # State management
    ├── error_handling.py  # DemoError (extends ActionableError)
    └── logging.py         # Logging configuration
```

## Testing

**25 BDD specs across 7 requirement classes** — organized by consumer requirement, not code structure.

| Requirement Class | Specs | Coverage |
|---|---|---|
| TestLoadingDemoScripts | 4 | File loading, not-found, empty, malformed |
| TestVariableHandling | 3 | Detection, substitution, passthrough |
| TestSequentialExecution | 4 | Present, execute, complete, post-complete |
| TestDemoStateManagement | 4 | Reset, progress, no-load-execute, no-load-next |
| TestErrorRecovery | 2 | Suggestions, format examples |
| TestMCPIntegration | 3 | Function signatures and discoverability |
| TestConversationalOrchestration | 5 | Full confirmation workflow with real fixtures |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — Execution model, components, and design decisions
- [Configuration](docs/CONFIGURATION.md) — Setup guide including Windows/WSL

## Related

- [workflow-orchestrator-mcp](https://github.com/grimlor/workflow-orchestrator-mcp) — Evolution for automated workflow execution with assertions and variable flow
- [actionable-errors](https://github.com/grimlor/actionable-errors) — Structured error library used by this project

## License

This project is licensed under the [MIT License](LICENSE).
