"""
Domain error types for demo-assistant-mcp

Extends the ``actionable-errors`` library with demo-specific error
categories and convenience factory methods that preserve the local API
surface while delegating structured error formatting to the library.
"""

from __future__ import annotations

from enum import StrEnum

from actionable_errors import ActionableError, ErrorType, ToolResult

_SERVICE = "demo-assistant"


class DemoErrorType(StrEnum):
    """Demo-specific error categories.

    A standalone ``StrEnum`` whose string values can be passed as the
    ``error_type`` argument to :class:`ActionableError` (which accepts
    ``ErrorType | str``).  Python forbids subclassing an enum that already
    has members, so this is a sibling enum rather than a child of
    :class:`ErrorType`.
    """

    NO_DEMO_LOADED = "no_demo_loaded"
    EMPTY_DEMO = "empty_demo"


class DemoError(ActionableError):
    """Actionable error with demo-specific factory methods.

    Every factory sets ``service`` to ``"demo-assistant"`` so that
    downstream consumers can identify the source without inspecting the
    error type.
    """

    # ------------------------------------------------------------------
    # Factory classmethods
    # ------------------------------------------------------------------

    @classmethod
    def file_not_found(cls, file_path: str) -> DemoError:
        """Create a file-not-found error."""
        return cls(
            error=f"Demo file not found at {file_path}",
            error_type=ErrorType.NOT_FOUND,
            service=_SERVICE,
            suggestion="Check that the file path is correct and the file exists",
        )

    @classmethod
    def invalid_format(
        cls,
        file_path: str,
        issue: str,
        *,
        example: str = "### 💬 COPILOT CHAT PROMPT:\n```\nYour prompt text here\n```",
    ) -> DemoError:
        """Create an invalid-format error with an example."""
        return cls(
            error=f"Invalid prompt format in {file_path}: {issue}",
            error_type=ErrorType.VALIDATION,
            service=_SERVICE,
            suggestion="Ensure each prompt follows the required format",
            context={"example": example},
        )

    @classmethod
    def empty_demo(
        cls,
        file_path: str,
        *,
        example: str = "### 💬 COPILOT CHAT PROMPT:\n```\nYour prompt text here\n```",
    ) -> DemoError:
        """Create an empty-demo error."""
        return cls(
            error=f"No prompts found in {file_path}",
            error_type=DemoErrorType.EMPTY_DEMO,
            service=_SERVICE,
            suggestion="Demo scripts must contain at least one prompt block",
            context={"example": example},
        )

    @classmethod
    def no_demo_loaded(cls, operation: str) -> DemoError:
        """Create a no-demo-loaded error."""
        return cls(
            error=f"Cannot {operation}: No demo has been loaded",
            error_type=DemoErrorType.NO_DEMO_LOADED,
            service=_SERVICE,
            suggestion="Load a demo script first using load_demo_script(file_path)",
        )


__all__ = [
    "ActionableError",
    "DemoError",
    "DemoErrorType",
    "ErrorType",
    "ToolResult",
]
