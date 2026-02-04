"""
Error handling utilities for demo-assistant-mcp

Provides ActionableError with AI-friendly guidance for demo script errors.
Adapted from pdp-dev-mcp pattern.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class ErrorType(str, Enum):
    """Error types specific to demo script operations"""
    FILE_NOT_FOUND = "file_not_found"
    INVALID_FORMAT = "invalid_format"
    NO_DEMO_LOADED = "no_demo_loaded"
    EMPTY_DEMO = "empty_demo"
    UNEXPECTED = "unexpected"


class ActionableError(Exception):
    """
    An error that includes a specific suggestion for how to resolve it.
    
    Used throughout the demo assistant to provide clear guidance to presenters
    and the AI agent when something goes wrong.
    
    Attributes:
        message: Human-readable error description
        suggestion: Quick action to resolve the error
        error_type: Categorized error type
        example: Optional example of correct format/usage
    """
    
    def __init__(
        self, 
        message: str, 
        suggestion: str = "",
        error_type: ErrorType = ErrorType.UNEXPECTED,
        example: Optional[str] = None
    ):
        """
        Initialize an actionable error.
        
        Args:
            message: Description of what went wrong
            suggestion: Specific guidance on how to fix it
            error_type: Category of error
            example: Optional example showing correct format
        """
        self.message = message
        self.suggestion = suggestion
        self.error_type = error_type
        self.example = example
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with suggestion and example if provided"""
        parts = [self.message]
        
        if self.suggestion:
            parts.append(f"\nSuggestion: {self.suggestion}")
        
        if self.example:
            parts.append(f"\nExample:\n{self.example}")
        
        return "".join(parts)
    
    def __str__(self) -> str:
        return self._format_message()
    
    # Factory methods for common demo errors
    
    @classmethod
    def file_not_found(cls, file_path: str) -> "ActionableError":
        """Create a file not found error"""
        return cls(
            message=f"Demo file not found at {file_path}",
            suggestion="Check that the file path is correct and the file exists",
            error_type=ErrorType.FILE_NOT_FOUND
        )
    
    @classmethod
    def invalid_format(cls, file_path: str, issue: str) -> "ActionableError":
        """Create an invalid format error with example"""
        return cls(
            message=f"Invalid prompt format in {file_path}: {issue}",
            suggestion="Ensure each prompt follows the required format",
            error_type=ErrorType.INVALID_FORMAT,
            example=(
                "### 💬 COPILOT CHAT PROMPT:\n"
                "```\n"
                "Your prompt text here\n"
                "```"
            )
        )
    
    @classmethod
    def empty_demo(cls, file_path: str) -> "ActionableError":
        """Create an empty demo error"""
        return cls(
            message=f"No prompts found in {file_path}",
            suggestion="Demo scripts must contain at least one prompt block",
            error_type=ErrorType.EMPTY_DEMO,
            example=(
                "### 💬 COPILOT CHAT PROMPT:\n"
                "```\n"
                "Your prompt text here\n"
                "```"
            )
        )
    
    @classmethod
    def no_demo_loaded(cls, operation: str) -> "ActionableError":
        """Create a no demo loaded error"""
        return cls(
            message=f"Cannot {operation}: No demo has been loaded",
            suggestion="Load a demo script first using load_demo_script(file_path)",
            error_type=ErrorType.NO_DEMO_LOADED
        )
