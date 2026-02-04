"""Shared pytest fixtures for demo-assistant-mcp tests"""

import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_demo_state():
    """Reset global demo state before each test"""
    from demo_assistant_mcp.common.demo_state import _demo_state
    _demo_state.file_path = ""
    _demo_state.prompts = []
    _demo_state.current_step = 0
    _demo_state.executed_count = 0
    _demo_state.pending_prompt = None
    _demo_state.variable_substitutions.clear()
    yield
    # Clean up after test as well
    _demo_state.file_path = ""
    _demo_state.prompts = []
    _demo_state.current_step = 0
    _demo_state.executed_count = 0
    _demo_state.pending_prompt = None
    _demo_state.variable_substitutions.clear()


@pytest.fixture
def valid_demo_markdown():
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
def empty_demo_markdown():
    """A markdown file with no prompts"""
    return """# Empty Demo

This demo has no executable prompts.
"""


@pytest.fixture
def malformed_demo_markdown():
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
def mock_file_system(valid_demo_markdown):
    """Mock file system operations"""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.read_text') as mock_read:
        mock_exists.return_value = True
        mock_read.return_value = valid_demo_markdown
        yield mock_exists, mock_read
