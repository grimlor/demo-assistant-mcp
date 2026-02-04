# Demo Assistant MCP Server - Design & Architecture

## Problem

Demo scripts contain prompts that must be manually copy-pasted into Copilot Chat during presentations. This creates friction, potential for typos, and breaks presenter flow.

## Solution

An MCP server that **orchestrates** demo execution—it queues prompts from markdown scripts, presents them for confirmation, and hands them off to Copilot for execution. The demo assistant does **not** invoke MCP tools directly; Copilot handles execution using whatever tools are available.

## How It Works

```
┌────────────────────────────────────────────────────────────┐
│  Presenter                                                 │
│     │                                                      │
│     ▼                                                      │
│  "Load my demo script"                                     │
│     │                                                      │
│     ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  demo-assistant-mcp (Orchestration)                 │   │
│  │                                                     │   │
│  │  load_demo_script() → Parse markdown, queue prompts │   │
│  │  next_demo_step()   → Present prompt for review     │   │
│  │  execute_demo_step()→ Return prompt to Copilot      │   │
│  │  reset_demo()       → Start over                    │   │
│  │  get_demo_state()   → Check progress                │   │
│  └─────────────────────────────────────────────────────┘   │
│     │                                                      │
│     ▼                                                      │
│  Copilot receives prompt → Invokes appropriate MCP tools   │
│  (GitHub, Azure DevOps, pdp-dev-mcp, etc.)                 │
│     │                                                      │
│     ▼                                                      │
│  Results displayed → Presenter narrates → Next prompt      │
└────────────────────────────────────────────────────────────┘
```

**Key insight:** The demo assistant is an orchestration layer. It manages the queue and confirmation workflow. Copilot handles actual tool execution.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Architecture** | Standalone MCP server | Reusable across any demo script |
| **Language** | Python | Matches existing MCP patterns |
| **Prompt Tag** | `### 💬 COPILOT CHAT PROMPT:` | Already used in existing demos |
| **Execution** | Sequential with confirmation | Presenter controls pacing |
| **State** | In-memory per session | No persistence needed |
| **Tool invocation** | Copilot, not demo-assistant | Leverage existing MCP infrastructure |

## Demo Script Format

~~~markdown
## Section Title

### 💬 COPILOT CHAT PROMPT:
```
Your prompt text here with optional [VARIABLES]
```

### 🎯 Expected Outcome:
Description of what should happen (future feature)
~~~

**Requirements:**
- Header must be exactly: `### 💬 COPILOT CHAT PROMPT:`
- Prompt must be in a fenced code block immediately after
- Variables use `[VARIABLE_NAME]` syntax (e.g., `[PR_ID]`, `[BRANCH_NAME]`)

## State Machine

```
┌──────────────┐  load_demo_script()  ┌──────────────┐
│   No Demo    │ ──────────────────▶  │    Loaded    │
└──────────────┘                      └──────────────┘
                                            │
                                   next_demo_step()
                                            ▼
                                      ┌──────────────┐
                                      │   Pending    │ ◀──┐
                                      │ Confirmation │    │
                                      └──────────────┘    │
                                            │             │
                                   execute_demo_step()    │
                                            ▼             │
                                      ┌──────────────┐    │
                                      │   Executed   │ ───┘ (if more prompts)
                                      └──────────────┘
                                            │
                                      (if demo_complete)
                                            ▼
                                      ┌──────────────┐
                                      │   Complete   │
                                      └──────────────┘
```

**State fields:**
- `current_step`: Index of next prompt to present (0-based)
- `executed_count`: Number of prompts executed
- `pending_prompt`: The prompt awaiting confirmation (if any)

**Transitions:**
- `next_demo_step()`: Sets `pending_prompt`, does NOT advance `current_step`
- `execute_demo_step()`: Clears `pending_prompt`, increments both `current_step` and `executed_count`

## Future Enhancements

- [ ] **Expected outcome validation** — Parse `### 🎯 Expected Outcome:` blocks, compare to results
- [ ] **Talking points** — Parse `### 🗣️ Talking Point:` blocks for presenter reference
- [ ] **Timing cues** — Parse `**⏱️ ~X minutes**` for pacing feedback
- [ ] **Jump to step** — `jump_to_demo_step(step_number)` tool
- [ ] **Demo checklist** — Interactive setup verification

## Files

```
src/demo_assistant_mcp/
├── server.py           # MCP server setup and tool registration
├── tools/
│   └── demo_tools.py   # Tool implementations
└── common/
    ├── demo_parser.py  # Markdown parsing
    ├── demo_state.py   # State management
    └── error_handling.py # ActionableError
```
