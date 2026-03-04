"""
Demo Assistant MCP Server

FastMCP-based server that exposes demo orchestration tools over the
MCP protocol (stdio transport).
"""

from __future__ import annotations

import logging

from actionable_errors import ToolResult
from fastmcp import FastMCP

from .common import ActionableError
from .tools.demo_tools import (
    execute_demo_step,
    get_demo_state,
    load_demo_script,
    next_demo_step,
    reset_demo,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP("demo-assistant-mcp")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def load_demo_script_tool(file_path: str) -> str:
    """Load and parse a demo markdown script file.

    Extracts prompts tagged with '### 💬 COPILOT CHAT PROMPT:' and prepares
    them for sequential execution.  Returns prompt count and the first prompt
    for review.

    Args:
        file_path: Absolute or relative path to the demo markdown file.
    """
    try:
        result = load_demo_script(file_path)
        return str(result)
    except ActionableError as e:
        logger.warning("load_demo_script failed: %s", e)
        return str(ToolResult.fail(e).to_dict())


@mcp.tool()
async def next_demo_step_tool() -> str:
    """Present the next prompt in the demo sequence without executing it.

    This allows the presenter to review and discuss the prompt before
    confirming execution.  Advances the viewing pointer but does not execute.
    Returns prompt text, variables detected, and readiness status.
    """
    try:
        result = next_demo_step()
        return str(result)
    except ActionableError as e:
        logger.warning("next_demo_step failed: %s", e)
        return str(ToolResult.fail(e).to_dict())


@mcp.tool()
async def execute_demo_step_tool(prompt_text: str | None = None) -> str:
    """Execute the currently pending prompt (or a modified version).

    If *prompt_text* is provided it will be used instead of the pending
    prompt, allowing variable substitution (e.g. replacing ``[PR_ID]``
    with the actual PR number).  After execution, automatically presents
    the next prompt if available.

    Args:
        prompt_text: Optional modified prompt text.  If not provided, uses
            the pending prompt as-is.
    """
    try:
        result = execute_demo_step(prompt_text)
        return str(result)
    except ActionableError as e:
        logger.warning("execute_demo_step failed: %s", e)
        return str(ToolResult.fail(e).to_dict())


@mcp.tool()
async def reset_demo_tool() -> str:
    """Reset the demo to the beginning.

    Clears execution history and returns to the first prompt.
    The demo script remains loaded.
    """
    try:
        result = reset_demo()
        return str(result)
    except ActionableError as e:
        logger.warning("reset_demo failed: %s", e)
        return str(ToolResult.fail(e).to_dict())


@mcp.tool()
async def get_demo_state_tool() -> str:
    """Get the current state of the loaded demo.

    Returns information about progress, current step, executed count,
    and remaining prompts.  Useful for status checks during the demo.
    """
    try:
        result = get_demo_state()
        return str(result)
    except ActionableError as e:
        logger.warning("get_demo_state failed: %s", e)
        return str(ToolResult.fail(e).to_dict())


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def run() -> None:
    """Synchronous entry point (used by pyproject.toml [project.scripts])."""
    mcp.run(transport="stdio")
