"""
Demo Assistant MCP Server

An MCP server for orchestrating demo script execution with GitHub Copilot.
Enables presenters to step through demo prompts with confirmation and variable substitution.
"""

from .common import ActionableError
from .common.demo_parser import parse_demo_markdown, DemoPrompt
from .common.demo_state import get_state, require_loaded_demo
from .tools.demo_tools import (
    load_demo_script,
    next_demo_step,
    execute_demo_step,
    reset_demo,
    get_demo_state
)

__version__ = "0.1.0"

__all__ = [
    "ActionableError",
    "DemoPrompt",
    "load_demo_script",
    "next_demo_step",
    "execute_demo_step",
    "reset_demo",
    "get_demo_state",
    "parse_demo_markdown",
]

