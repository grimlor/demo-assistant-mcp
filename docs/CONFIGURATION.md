# Demo Assistant MCP Server - Configuration

## VS Code MCP Configuration

Add this to your VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "mcp.servers": {
    "demo-assistant": {
      "command": "demo-assistant-mcp",
      "env": {},
      "description": "Orchestrate demo script execution with prompt queuing and variable substitution"
    }
  }
}
```

### For Development (using local checkout)

If testing from the repository without global installation:

```json
{
  "mcp.servers": {
    "demo-assistant": {
      "command": "uv",
      "args": ["run", "demo-assistant-mcp"],
      "cwd": "/path/to/demo-assistant-mcp",
      "description": "Orchestrate demo script execution (dev mode)"
    }
  }
}
```

### For Windows with WSL (local development)

If you're developing on Windows and running the server in WSL:

```json
{
  "mcp.servers": {
    "demo-assistant": {
      "command": "wsl.exe",
      "args": [
        "zsh",
        "-c",
        "cd /home/username/src/demo-assistant-mcp && .venv/bin/python -m demo_assistant_mcp.server"
      ],
      "type": "stdio",
      "description": "Orchestrate demo script execution (WSL)"
    }
  }
}
```

*Replace `/home/username/src/demo-assistant-mcp` with your actual WSL path and adjust the shell (`zsh`/`bash`) as needed.*

## Usage Example

Once configured, you can use Copilot Chat to orchestrate your demos:

```
You: Load /path/to/demo_01_ado_pr_workflows.md

Copilot: ✅ Loaded 7 prompts from demo. 
         Ready! Step 1: "What Azure DevOps repository am I working in?"
         Ready to execute?

You: confirm

Copilot: [Executes prompt by calling Azure DevOps tools]
         ✅ Step 1 complete.
         Next: Step 2: "Analyze comments on PR [PR_ID]" 
         (Note: [PR_ID] needs value) Ready to execute?

You: Execute with PR ID 14679218

Copilot: [Executes with substituted value]
         ...
```

## Available Tools

- **load_demo_script** - Load and parse a demo markdown file
- **next_demo_step** - Present next prompt for confirmation
- **execute_demo_step** - Execute current/modified prompt
- **reset_demo** - Reset demo to beginning
- **get_demo_state** - Get current demo progress

## Demo Script Format

Prompts must be tagged with:

```markdown
### 💬 COPILOT CHAT PROMPT:
\```
Your prompt text here
Can include variables like [PR_ID] or [BRANCH_NAME]
\```
```

See `demo_01_ado_pr_workflows.md` in the parent directory for a complete example.
