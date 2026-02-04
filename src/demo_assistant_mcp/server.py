"""
MCP Server for Demo Assistant

Provides tools for orchestrating demo script execution with GitHub Copilot.
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.demo_tools import (
    load_demo_script,
    next_demo_step,
    execute_demo_step,
    reset_demo,
    get_demo_state,
)
from .common import ActionableError

# Set up logging
logger = logging.getLogger("demo-assistant-mcp")
logger.setLevel(logging.INFO)

# Create server instance
app = Server("demo-assistant-mcp")


# Tool definitions for MCP
TOOLS = [
    Tool(
        name="load_demo_script",
        description=(
            "Load and parse a demo markdown script file. "
            "Extracts prompts tagged with '### 💬 COPILOT CHAT PROMPT:' and prepares them for sequential execution. "
            "Returns prompt count and the first prompt for review."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the demo markdown file"
                }
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="next_demo_step",
        description=(
            "Present the next prompt in the demo sequence without executing it. "
            "This allows the presenter to review and discuss the prompt before confirming execution. "
            "Advances the viewing pointer but does not execute. "
            "Returns prompt text, variables detected, and readiness status."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="execute_demo_step",
        description=(
            "Execute the currently pending prompt (or a modified version). "
            "If prompt_text is provided, it will be used instead of the pending prompt, "
            "allowing variable substitution (e.g., replacing [PR_ID] with actual PR number). "
            "After execution, automatically presents the next prompt if available."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "prompt_text": {
                    "type": "string",
                    "description": "Optional modified prompt text. If not provided, uses the pending prompt as-is."
                }
            },
            "required": []
        }
    ),
    Tool(
        name="reset_demo",
        description=(
            "Reset the demo to the beginning. "
            "Clears execution history and returns to the first prompt. "
            "The demo script remains loaded."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="get_demo_state",
        description=(
            "Get the current state of the loaded demo. "
            "Returns information about progress, current step, executed count, and remaining prompts. "
            "Useful for status checks during the demo."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available demo orchestration tools"""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls from the MCP client.
    
    Routes to appropriate demo tool function and handles errors.
    """
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if name == "load_demo_script":
            result = load_demo_script(arguments["file_path"])
        elif name == "next_demo_step":
            result = next_demo_step()
        elif name == "execute_demo_step":
            prompt_text = arguments.get("prompt_text")
            result = execute_demo_step(prompt_text)
        elif name == "reset_demo":
            result = reset_demo()
        elif name == "get_demo_state":
            result = get_demo_state()
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        logger.info(f"Tool {name} succeeded")
        return [TextContent(type="text", text=str(result))]
        
    except ActionableError as e:
        # Return actionable errors as structured text
        logger.warning(f"Tool {name} failed with ActionableError: {e}")
        error_response = {
            "success": False,
            "error": str(e),
            "error_type": e.error_type.value,
        }
        return [TextContent(type="text", text=str(error_response))]
        
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Tool {name} failed with unexpected error: {e}", exc_info=True)
        error_response = {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unexpected",
        }
        return [TextContent(type="text", text=str(error_response))]


async def main():
    """Run the MCP server via stdio"""
    logger.info("Starting demo-assistant-mcp server")
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Entry point for the server"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
