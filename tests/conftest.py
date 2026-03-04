"""Shared pytest fixtures for demo-assistant-mcp tests"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from demo_assistant_mcp import load_demo_script
from demo_assistant_mcp.common.demo_state import get_state


def _clear_state() -> None:
    """Reset global demo state fields to defaults."""
    state = get_state()
    state.file_path = ""
    state.prompts = []
    state.current_step = 0
    state.executed_count = 0
    state.pending_prompt = None
    state.variable_substitutions.clear()


@pytest.fixture(autouse=True)
def reset_demo_state() -> Generator[None]:
    """Reset global demo state before each test"""
    _clear_state()
    yield
    _clear_state()


@pytest.fixture
def valid_demo_markdown() -> str:
    """A well-formed demo script with multiple prompts"""
    return """# Demo Script Title

## Setup Section

Some introductory text.

### 💬 COPILOT CHAT PROMPT:
```
What repository am I working in?
```

### 🎯 Expected Outcome:
Should show repository details.

## Main Demo Section

### 💬 COPILOT CHAT PROMPT:
```
Analyze PR [PR_ID] and show me the comments
```

### 💬 COPILOT CHAT PROMPT:
```
Create a new PR for branch [BRANCH_NAME]
```
"""


@pytest.fixture
def empty_demo_markdown() -> str:
    """A markdown file with no prompts"""
    return """# Empty Demo

This demo has no executable prompts.
"""


@pytest.fixture
def malformed_demo_markdown() -> str:
    """A markdown file with malformed prompt blocks"""
    return """# Bad Demo

### 💬 COPILOT CHAT PROMPT:
This prompt is missing code block markers

### COPILOT CHAT PROMPT:
```
This one is missing the emoji marker
```
"""


@pytest.fixture
def mock_file_system(valid_demo_markdown: str) -> Generator[None]:
    """Mock file system operations"""
    with patch("pathlib.Path.exists") as mock_exists, patch("pathlib.Path.read_text") as mock_read:
        mock_exists.return_value = True
        mock_read.return_value = valid_demo_markdown
        yield


@pytest.fixture
def code_block_opens_but_never_closes() -> str:
    """A markdown file with a prompt header followed by an unterminated code block."""
    return "# Demo\n\n### \U0001f4ac COPILOT CHAT PROMPT:\n```\nThis code block never closes\n"


@pytest.fixture
def loaded_demo_with_variables() -> Generator[None]:
    """Load a demo and pre-populate variable_substitutions on the state."""
    markdown = (
        "# Demo\n\n"
        "### \U0001f4ac COPILOT CHAT PROMPT:\n"
        "```\n"
        "Analyze PR [PR_ID] on branch [BRANCH]\n"
        "```\n"
    )
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value=markdown),
    ):
        load_demo_script("/path/to/demo.md")

    state = get_state()
    state.variable_substitutions = {"PR_ID": "42", "BRANCH": "main"}
    yield
