"""
Demo state management

Tracks the current position in a demo, which prompts have been executed,
and manages the queue of pending prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .error_handling import DemoError

if TYPE_CHECKING:
    from .demo_parser import DemoPrompt


@dataclass
class DemoState:
    """
    Manages the state of a demo session.

    Tracks which demo is loaded, current position, execution history,
    and the pending prompt awaiting confirmation.
    """

    file_path: str = ""
    prompts: list[DemoPrompt] = field(default_factory=list)
    current_step: int = 0  # Index in prompts list (0-based)
    executed_count: int = 0
    pending_prompt: DemoPrompt | None = None
    variable_substitutions: dict[str, str] = field(default_factory=dict)

    @property
    def total_prompts(self) -> int:
        """Total number of prompts in the demo"""
        return len(self.prompts)

    @property
    def prompts_remaining(self) -> int:
        """Number of prompts not yet executed"""
        return self.total_prompts - self.executed_count

    @property
    def is_complete(self) -> bool:
        """Check if all prompts have been executed"""
        return self.executed_count >= self.total_prompts

    @property
    def is_loaded(self) -> bool:
        """Check if a demo has been loaded"""
        return bool(self.file_path and self.prompts)

    def reset(self) -> None:
        """Reset demo to beginning while keeping prompts loaded"""
        self.current_step = 0
        self.executed_count = 0
        self.pending_prompt = None
        self.variable_substitutions.clear()

    def get_current_prompt(self) -> DemoPrompt | None:
        """Get the prompt at the current step"""
        if 0 <= self.current_step < self.total_prompts:
            return self.prompts[self.current_step]
        return None

    def advance(self) -> None:
        """Mark step as executed (don't advance current_step, that's done in next_demo_step)"""
        self.executed_count += 1
        self.pending_prompt = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "total_prompts": self.total_prompts,
            "current_step": self.current_step,
            "executed_count": self.executed_count,
            "prompts_remaining": self.prompts_remaining,
            "is_complete": self.is_complete,
            "pending_prompt": {
                "text": self.pending_prompt.text,
                "step_number": self.pending_prompt.step_number,
                "has_variables": self.pending_prompt.has_variables,
                "variables": list(self.pending_prompt.variables),
            }
            if self.pending_prompt
            else None,
        }


# Global state instance (one demo session at a time)
_demo_state = DemoState()


def get_state() -> DemoState:
    """Get the current demo state"""
    return _demo_state


def require_loaded_demo() -> DemoState:
    """
    Get the current state and verify a demo is loaded.

    Returns:
        The current demo state

    Raises:
        DemoError: If no demo has been loaded
    """
    state = get_state()
    if not state.is_loaded:
        raise DemoError.no_demo_loaded("proceed with operation")
    return state
