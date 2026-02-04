# Demo Assistant MCP Server

An MCP server for orchestrating demo script execution with GitHub Copilot. Enables presenters to step through demo prompts with confirmation and variable substitution.

## Quick Install

[<img src="https://img.shields.io/badge/VS_Code-VS_Code?style=flat-square&label=Install%20Server&color=0098FF" alt="Install in VS Code">](https://vscode.dev/redirect?url=vscode%3Amcp/install%3F%257B%2522name%2522%253A%2520%2522demo-assistant-mcp%2522%252C%2520%2522command%2522%253A%2520%2522uvx%2522%252C%2520%2522args%2522%253A%2520%255B%2522--from%2522%252C%2520%2522git%252Bhttps%253A//github.com/grimlor/demo-assistant-mcp%2522%252C%2520%2522demo-assistant-mcp%2522%255D%252C%2520%2522type%2522%253A%2520%2522stdio%2522%257D) [<img alt="Install in VS Code Insiders" src="https://img.shields.io/badge/VS_Code_Insiders-VS_Code_Insiders?style=flat-square&label=Install%20Server&color=24bfa5">](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp/install%3F%257B%2522name%2522%253A%2520%2522demo-assistant-mcp%2522%252C%2520%2522command%2522%253A%2520%2522uvx%2522%252C%2520%2522args%2522%253A%2520%255B%2522--from%2522%252C%2520%2522git%252Bhttps%253A//github.com/grimlor/demo-assistant-mcp%2522%252C%2520%2522demo-assistant-mcp%2522%255D%252C%2520%2522type%2522%253A%2520%2522stdio%2522%257D)

*Click a badge above to install with one click, or follow manual installation below.*

## Status

✅ **MVP Complete** - Ready for testing!

- ✅ Phase 0: BDD Specification (20 test scenarios)
- ✅ Phase 1: Project Setup  
- ✅ Phase 2-4: Implementation (all tests passing)
- ✅ Phase 5: Server Integration
- ✅ Phase 6: Documentation

## Features

- **Sequential Execution**: Step through prompts one at a time with confirmation
- **Variable Substitution**: Dynamic values like `[PR_ID]` or `[BRANCH_NAME]`
- **State Management**: Track progress, reset, query status
- **Error Handling**: Actionable errors with suggestions
- **Format Validation**: Strict parsing with helpful error messages

## Installation

### Quick Install (Recommended)

Click one of the badges at the top to automatically install in VS Code!

### Manual Installation

#### Linux/macOS

```bash
# From source (development)
cd demo-assistant-mcp
uv sync --all-extras

# The command will be available in the venv
demo-assistant-mcp
```

#### Windows with WSL

If you're developing on Windows and want to run the server in WSL, see [Configuration Guide](docs/CONFIGURATION.md#for-windows-with-wsl-local-development) for WSL-specific setup.

## VS Code Configuration

Add to your VS Code MCP settings:

```json
{
  "mcp.servers": {
    "demo-assistant": {
      "command": "uv",
      "args": ["run", "demo-assistant-mcp"],
      "cwd": "/absolute/path/to/demo-assistant-mcp",
      "description": "Orchestrate demo script execution"
    }
  }
}
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed setup instructions.

## Demo Script Format

Create markdown files with tagged prompts:

```markdown
### 💬 COPILOT CHAT PROMPT:
\```
What Azure DevOps repository am I working in?
\```

### 💬 COPILOT CHAT PROMPT:
\```
Analyze PR [PR_ID] and show me the comments
\```
```

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

## Available Tools

| Tool | Purpose |
|------|---------|
| `load_demo_script` | Load and parse demo markdown file |
| `next_demo_step` | Present next prompt for review |
| `execute_demo_step` | Execute current/modified prompt |
| `reset_demo` | Reset to beginning |
| `get_demo_state` | Query current progress |

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check

# Format
uv run ruff format
```

## Architecture

```
demo-assistant-mcp/
├── src/demo_assistant_mcp/
│   ├── server.py              # MCP server entry point
│   ├── tools/
│   │   └── demo_tools.py      # Tool implementations
│   └── common/
│       ├── demo_parser.py     # Markdown parsing
│       ├── demo_state.py      # State management
│       ├── error_handling.py  # ActionableError
│       └── logging.py         # Logging setup
├── tests/
│   ├── test_demo_assistant.py # BDD test suite (20 scenarios)
│   └── conftest.py            # Pytest fixtures
└── docs/
    └── CONFIGURATION.md       # Setup guide
```

## Testing

**Test Coverage: 100% (20/20 scenarios passing)**

- ✅ Loading demo scripts (4 scenarios)
- ✅ Variable handling (3 scenarios)
- ✅ Sequential execution (4 scenarios)
- ✅ State management (4 scenarios)
- ✅ Error recovery (2 scenarios)
- ✅ MCP integration (3 scenarios)

## Example

See `../demo_01_ado_pr_workflows.md` for a complete demo script used with the pdp-dev-mcp Azure DevOps tools.

## Author

Jack Pines (github@jackpines.info)
