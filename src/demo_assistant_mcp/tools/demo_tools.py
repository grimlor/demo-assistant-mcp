"""
MCP Tools for demo orchestration

Provides the core functions that will be exposed as MCP tools:
- load_demo_script: Load and parse a demo markdown file
- next_demo_step: Present the next prompt for confirmation
- execute_demo_step: Execute the current/modified prompt
- reset_demo: Reset demo to beginning
- get_demo_state: Get current demo state
"""

from __future__ import annotations

from typing import Any

from ..common import DemoError, DemoErrorType
from ..common.demo_parser import parse_demo_markdown
from ..common.demo_state import get_state, require_loaded_demo


def load_demo_script(file_path: str) -> dict[str, Any]:
    """
    Load and parse a demo markdown file.

    Args:
        file_path: Path to the demo markdown file

    Returns:
        Dictionary with:
            - success: bool
            - prompt_count: int
            - first_prompt: dict with text, step_number, etc.

    Raises:
        DemoError: If file not found, invalid format, or no prompts
    """
    # Parse the markdown file
    prompts = parse_demo_markdown(file_path)

    # Initialize state
    state = get_state()
    state.file_path = file_path
    state.prompts = prompts
    state.current_step = 0
    state.executed_count = 0
    state.pending_prompt = None
    state.variable_substitutions.clear()

    # Prepare first prompt info
    first_prompt = prompts[0]

    return {
        "success": True,
        "prompt_count": len(prompts),
        "first_prompt": {
            "text": first_prompt.text,
            "step_number": first_prompt.step_number,
            "section_title": first_prompt.section_title,
            "has_variables": first_prompt.has_variables,
            "variables": list(first_prompt.variables),
        },
    }


def next_demo_step() -> dict[str, Any]:
    """
    Present the next prompt for confirmation without executing it.
    Advances the current_step pointer to present the next unviewed prompt.

    Returns:
        Dictionary with:
            - prompt_text: str
            - status: "awaiting_confirmation" or "demo_complete"
            - step_number: int (if available)
            - has_variables: bool
            - variables: list of variable names
            - message: str (if demo complete)

    Raises:
        DemoError: If no demo has been loaded
    """
    state = require_loaded_demo()

    # Check if all prompts have been viewed or executed
    if state.current_step >= state.total_prompts or state.executed_count >= state.total_prompts:
        return {"status": "demo_complete", "message": "Demo complete! No more prompts to view."}

    # Get current prompt
    prompt = state.prompts[state.current_step]

    # Mark as pending (do NOT advance current_step here)
    state.pending_prompt = prompt

    return {
        "prompt_text": prompt.text,
        "status": "awaiting_confirmation",
        "step_number": prompt.step_number,
        "total_steps": state.total_prompts,
        "has_variables": prompt.has_variables,
        "variables": list(prompt.variables),
    }


def execute_demo_step(prompt_text: str | None = None) -> dict[str, Any]:
    """
    Execute the current prompt (or a modified version).

    Args:
        prompt_text: Optional modified prompt text. If None, uses pending prompt.

    Returns:
        Dictionary with:
            - executed: bool
            - executed_prompt: str
            - step_completed: int
            - next_prompt: dict (if more prompts remain)
            - demo_complete: bool
            - total_steps: int

    Raises:
        DemoError: If no demo has been loaded or no pending prompt
    """
    state = require_loaded_demo()

    # Get the prompt to execute
    if prompt_text:
        # User provided modified text
        executed_text = prompt_text
    elif state.pending_prompt:
        # Use pending prompt
        executed_text = state.pending_prompt.text
    else:
        # No pending prompt - try to get current
        prompt = state.get_current_prompt()
        if not prompt:
            raise DemoError(
                error="No prompt available to execute",
                error_type=DemoErrorType.NO_DEMO_LOADED,
                service="demo-assistant",
                suggestion="Call next_demo_step() first to load a prompt",
            )
        executed_text = prompt.text

    # --- Variable substitution (simple placeholder logic) ---
    substitutions = state.variable_substitutions or {}
    for var, value in substitutions.items():
        executed_text = executed_text.replace(f"[{var}]", value)

    # Mark step as complete and advance current_step
    state.advance()
    state.current_step += 1

    # Check if there are more prompts
    result = {
        "executed": True,
        "executed_prompt": executed_text,
        "step_completed": state.executed_count,
        "total_steps": state.total_prompts,
        "demo_complete": state.is_complete,
    }

    # If more prompts, automatically present next
    if not state.is_complete:
        next_prompt = state.get_current_prompt()
        if next_prompt:
            result["next_prompt"] = {
                "text": next_prompt.text,
                "step_number": next_prompt.step_number,
                "has_variables": next_prompt.has_variables,
                "variables": list(next_prompt.variables),
            }

    return result


def reset_demo() -> dict[str, Any]:
    """
    Reset the demo to the beginning.

    Returns:
        Dictionary with:
            - success: bool
            - current_step: int (should be 0)
            - executed_count: int (should be 0)

    Raises:
        DemoError: If no demo has been loaded
    """
    state = require_loaded_demo()
    state.reset()

    return {
        "success": True,
        "current_step": state.current_step,
        "executed_count": state.executed_count,
    }


def get_demo_state() -> dict[str, Any]:
    """
    Get the current state of the demo.

    Returns:
        Dictionary with state information

    Raises:
        DemoError: If no demo has been loaded
    """
    state = require_loaded_demo()
    return state.to_dict()
