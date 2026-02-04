"""
BDD-Style Specification for Demo Assistant MCP Server

This specification describes WHAT the demo assistant does, WHY it exists,
and FOR WHOM it's designed - without dictating HOW it's implemented.

Target User: Technical presenters giving live demos of MCP tools
Problem: Manual copy-paste of demo prompts creates friction and typos
Solution: Orchestrate demo execution with prompt queuing and confirmation

Only I/O boundaries (file system) are mocked - internal logic is tested via behavior.
"""

import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch


# ============================================================================
# Scenario 1: Loading Demo Scripts
# WHO: Presenter starting a demo
# WHY: Need to load and parse demo prompts before execution
# WHAT: Load demo file and extract all executable prompts
# ============================================================================

class TestLoadingDemoScripts:
    """
    As a presenter,
    I want to load my demo script,
    So that I can execute prompts in sequence during my demo.
    """

    def test_load_valid_demo_returns_prompt_count(self, mock_file_system):
        """
        Given a valid demo markdown file with 3 prompts
        When I load the demo script
        Then I should receive confirmation with prompt count
        And the first prompt should be presented for confirmation
        """
        from demo_assistant_mcp import load_demo_script
        
        result = load_demo_script("/path/to/demo.md")
        
        assert result["success"] is True
        assert result["prompt_count"] == 3
        assert "first_prompt" in result
        assert result["first_prompt"]["text"] == "What repository am I working in?"
        assert result["first_prompt"]["step_number"] == 1

    def test_load_demo_with_file_not_found(self):
        """
        Given a demo file path that doesn't exist
        When I attempt to load the demo
        Then I should receive an actionable error
        And the error should suggest checking the file path
        """
        from demo_assistant_mcp import load_demo_script, ActionableError
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ActionableError) as exc_info:
                load_demo_script("/nonexistent/demo.md")
            
            assert "not found" in str(exc_info.value).lower()
            assert "check" in str(exc_info.value).lower()

    def test_load_empty_demo_fails_gracefully(self, empty_demo_markdown):
        """
        Given a markdown file with no executable prompts
        When I load the demo
        Then I should receive an actionable error
        And the error should explain that no prompts were found
        """
        from demo_assistant_mcp import load_demo_script, ActionableError
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=empty_demo_markdown):
            with pytest.raises(ActionableError) as exc_info:
                load_demo_script("/path/to/empty.md")
            
            assert "no prompts" in str(exc_info.value).lower()

    def test_load_malformed_demo_identifies_issues(self, malformed_demo_markdown):
        """
        Given a markdown file with malformed prompt blocks
        When I load the demo
        Then I should receive an actionable error
        And the error should identify what's wrong with the format
        """
        from demo_assistant_mcp import load_demo_script, ActionableError
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=malformed_demo_markdown):
            with pytest.raises(ActionableError) as exc_info:
                load_demo_script("/path/to/malformed.md")
            
            error_msg = str(exc_info.value).lower()
            assert "format" in error_msg or "invalid" in error_msg


# ============================================================================
# Scenario 2: Variable Detection and Substitution
# WHO: Presenter working with dynamic data (PR IDs, branch names)
# WHY: Demo data changes between sessions
# WHAT: Detect variables in prompts and support substitution
# ============================================================================

class TestVariableHandling:
    """
    As a presenter,
    I want to use placeholder variables in my prompts,
    So that I can substitute current values during the demo.
    """

    def test_detect_variables_in_prompt(self, mock_file_system):
        """
        Given a demo with prompts containing [PR_ID] and [BRANCH_NAME]
        When I load the demo and view a prompt
        Then variables should be detected and reported
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        next_demo_step()  # Present first prompt
        execute_demo_step()  # Execute first prompt to advance
        
        result = next_demo_step()  # Now get second prompt with [PR_ID]
        
        assert result["has_variables"] is True
        assert "[PR_ID]" in result["variables"]

    def test_execute_prompt_with_variable_substitution(self, mock_file_system):
        """
        Given a prompt with [PR_ID] variable
        When I execute with substitution: "Analyze PR 12345..."
        Then the executed prompt should have the variable replaced
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        next_demo_step()  # Move to second prompt
        
        result = execute_demo_step(prompt_text="Analyze PR 12345 and show me the comments")
        
        assert result["executed_prompt"] == "Analyze PR 12345 and show me the comments"
        assert "[PR_ID]" not in result["executed_prompt"]

    def test_execute_prompt_without_substitution_keeps_original(self, mock_file_system):
        """
        Given a prompt without variables
        When I execute without modification
        Then the original prompt text should be executed
        """
        from demo_assistant_mcp import load_demo_script, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        
        result = execute_demo_step()  # Execute first prompt as-is
        
        assert result["executed_prompt"] == "What repository am I working in?"


# ============================================================================
# Scenario 3: Sequential Execution with Confirmation
# WHO: Presenter stepping through a demo
# WHY: Need to discuss each prompt before executing
# WHAT: Present prompts one at a time, await confirmation, execute
# ============================================================================

class TestSequentialExecution:
    """
    As a presenter,
    I want to step through prompts with confirmation,
    So that I can discuss each step before executing it.
    """

    def test_next_step_presents_prompt_without_executing(self, mock_file_system):
        """
        Given a loaded demo
        When I call next_demo_step
        Then the next prompt should be presented
        And it should NOT be executed automatically
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, get_demo_state
        
        load_demo_script("/path/to/demo.md")
        result = next_demo_step()
        
        assert result["prompt_text"] == "What repository am I working in?"
        assert result["status"] == "awaiting_confirmation"
        
        # Verify execution hasn't happened by checking state
        state = get_demo_state()
        assert state["executed_count"] == 0

    def test_execute_step_runs_current_prompt(self, mock_file_system):
        """
        Given a prompt awaiting confirmation
        When I call execute_demo_step
        Then the prompt should be executed
        And the next prompt should be automatically presented
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        next_demo_step()
        
        result = execute_demo_step()
        
        assert result["executed"] is True
        assert result["step_completed"] == 1
        assert "next_prompt" in result
        assert result["next_prompt"]["text"] == "Analyze PR [PR_ID] and show me the comments"

    def test_complete_demo_sequence(self, mock_file_system):
        """
        Given a demo with 3 prompts
        When I execute all prompts in sequence
        Then I should get confirmation after the last prompt
        And the demo should be marked complete
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        
        # Execute all 3 prompts
        for i in range(3):
            next_demo_step()
            result = execute_demo_step()
        
        # After last prompt, should indicate completion
        assert result["demo_complete"] is True
        assert result["total_steps"] == 3

    def test_next_step_after_completion_indicates_done(self, mock_file_system):
        """
        Given a completed demo
        When I call next_demo_step
        Then I should receive a message indicating the demo is complete
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step
        
        load_demo_script("/path/to/demo.md")
        
        # Complete all steps
        for i in range(3):
            next_demo_step()
            execute_demo_step()
        
        result = next_demo_step()
        
        assert result["status"] == "demo_complete"
        assert "no more prompts" in result["message"].lower()


# ============================================================================
# Scenario 4: Demo State Management
# WHO: Presenter managing demo flow
# WHY: Need to track position, reset, and handle errors
# WHAT: Maintain state, support reset, handle edge cases
# ============================================================================

class TestDemoStateManagement:
    """
    As a presenter,
    I want to manage my demo state,
    So that I can reset, track progress, and recover from issues.
    """

    def test_reset_demo_returns_to_beginning(self, mock_file_system):
        """
        Given a demo in progress (some prompts executed)
        When I call reset_demo
        Then the demo should return to the first prompt
        And execution history should be cleared
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step, reset_demo
        
        load_demo_script("/path/to/demo.md")
        next_demo_step()
        execute_demo_step()
        next_demo_step()
        
        result = reset_demo()
        
        assert result["success"] is True
        assert result["current_step"] == 0
        assert result["executed_count"] == 0

    def test_get_demo_state_shows_progress(self, mock_file_system):
        """
        Given a demo with some prompts executed
        When I query the demo state
        Then I should see current position and progress
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step, get_demo_state
        
        load_demo_script("/path/to/demo.md")
        next_demo_step()
        execute_demo_step()
        
        state = get_demo_state()
        
        assert state["total_prompts"] == 3
        assert state["executed_count"] == 1
        assert state["current_step"] == 1
        assert state["prompts_remaining"] == 2

    def test_execute_without_loading_demo_fails(self):
        """
        Given no demo has been loaded
        When I attempt to execute a step
        Then I should receive an actionable error
        And the error should instruct me to load a demo first
        """
        from demo_assistant_mcp import execute_demo_step, ActionableError
        
        with pytest.raises(ActionableError) as exc_info:
            execute_demo_step()
        
        assert "load" in str(exc_info.value).lower()
        assert "demo" in str(exc_info.value).lower()

    def test_next_step_without_loading_demo_fails(self):
        """
        Given no demo has been loaded
        When I attempt to advance to next step
        Then I should receive an actionable error
        """
        from demo_assistant_mcp import next_demo_step, ActionableError
        
        with pytest.raises(ActionableError) as exc_info:
            next_demo_step()
        
        assert "load" in str(exc_info.value).lower()


# ============================================================================
# Scenario 5: Error Recovery
# WHO: Presenter encountering issues during demo
# WHY: Demos must be resilient to expected failures
# WHAT: Provide actionable errors and recovery paths
# ============================================================================

class TestErrorRecovery:
    """
    As a presenter,
    I want clear error messages with recovery suggestions,
    So that I can quickly fix issues during my demo.
    """

    def test_actionable_error_includes_suggestion(self):
        """
        Given an error condition (e.g., file not found)
        When an ActionableError is raised
        Then it should include a specific suggestion for resolution
        """
        from demo_assistant_mcp import ActionableError
        
        error = ActionableError(
            "Demo file not found at /path/to/demo.md",
            suggestion="Check that the file path is correct and the file exists"
        )
        
        assert "not found" in str(error)
        assert error.suggestion == "Check that the file path is correct and the file exists"

    def test_invalid_prompt_format_gives_format_example(self, malformed_demo_markdown):
        """
        Given a demo with invalid prompt format
        When I load the demo
        Then the error should include an example of correct format
        """
        from demo_assistant_mcp import load_demo_script, ActionableError
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=malformed_demo_markdown):
            with pytest.raises(ActionableError) as exc_info:
                load_demo_script("/path/to/demo.md")
            
            assert "### 💬 COPILOT CHAT PROMPT:" in str(exc_info.value)


# ============================================================================
# Integration Contract Tests
# These tests define the expected behavior when integrated with MCP
# ============================================================================

class TestMCPIntegration:
    """
    As an MCP server,
    I need to provide tools that Copilot can discover and call,
    So that presenters can use natural language to control demos.
    """

    def test_load_demo_script_tool_signature(self):
        """
        The load_demo_script tool should accept a file_path parameter
        and return a structured result for Copilot to process.
        """
        from demo_assistant_mcp import load_demo_script
        import inspect
        
        sig = inspect.signature(load_demo_script)
        assert "file_path" in sig.parameters
        assert sig.parameters["file_path"].annotation == str

    def test_next_demo_step_tool_signature(self):
        """
        The next_demo_step tool should take no required parameters
        and return the next prompt details.
        """
        from demo_assistant_mcp import next_demo_step
        import inspect
        
        sig = inspect.signature(next_demo_step)
        required_params = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]
        assert len(required_params) == 0

    def test_execute_demo_step_tool_signature(self):
        """
        The execute_demo_step tool should accept an optional prompt_text
        to allow modification before execution.
        """
        from demo_assistant_mcp import execute_demo_step
        import inspect
        
        sig = inspect.signature(execute_demo_step)
        assert "prompt_text" in sig.parameters
        # Should be optional
        assert sig.parameters["prompt_text"].default is not None or \
               sig.parameters["prompt_text"].annotation == Optional[str]
