"""
Demo Assistant MCP Server

An MCP server for orchestrating demo script execution with GitHub Copilot.
Enables presenters to step through demo prompts with confirmation and variable substitution.
"""

from __future__ import annotations

from .common import ActionableError, DemoError, DemoErrorType, ErrorType, ToolResult
from .common.demo_parser import DemoPrompt, parse_demo_markdown
from .common.demo_state import get_state, require_loaded_demo
from .tools.demo_tools import (
    execute_demo_step,
    get_demo_state,
    load_demo_script,
    next_demo_step,
    reset_demo,
)

__version__ = "0.1.0"

__all__ = [
    "ActionableError",
    "DemoError",
    "DemoErrorType",
    "DemoPrompt",
    "ErrorType",
    "ToolResult",
    "execute_demo_step",
    "get_demo_state",
    "get_state",
    "load_demo_script",
    "next_demo_step",
    "parse_demo_markdown",
    "require_loaded_demo",
    "reset_demo",
]
