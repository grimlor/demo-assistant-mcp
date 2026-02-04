"""
BDD-Style Specification: Conversational Orchestration for Demo Assistant MCP Server

These tests extend the existing suite to explicitly verify the conversational confirmation workflow:
- Prompts are presented for review
- Assistant awaits explicit confirmation before execution
- User can modify prompt before confirming
- Sequence of user/assistant actions matches intended demo flow
"""

import pytest
from unittest.mock import patch

import pytest

class TestConversationalOrchestration:
    """
    As a presenter,
    I want the assistant to present each prompt for confirmation before execution,
    So that I can review, modify, and control the demo flow interactively.
    """

    def test_prompt_presented_and_waits_for_confirmation(self):
        """
        Given a loaded demo script
        When I advance to the next prompt
        Then the assistant should present the prompt for review
        And the system should be in a 'waiting for confirmation' state
        And the prompt should NOT be executed yet
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, get_demo_state

        load_demo_script("tests/fixtures/test_demo.md")
        result = next_demo_step()

        assert result["prompt_text"] == "What is the current date and time?"
        assert result["status"] == "awaiting_confirmation"
        state = get_demo_state()
        assert state["executed_count"] == 0

    def test_prompt_executed_only_after_confirmation(self):
        """
        Given a prompt is awaiting confirmation
        When I confirm execution
        Then the assistant should execute the prompt
        And advance to the next prompt
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step, get_demo_state

        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()
        result = execute_demo_step()

        assert result["executed"] is True
        assert result["step_completed"] == 1
        state = get_demo_state()
        assert state["executed_count"] == 1

    def test_user_can_modify_prompt_before_execution(self):
        """
        Given a prompt with a variable (e.g., [FILENAME])
        When I provide a modified prompt text and confirm
        Then the assistant should execute the modified prompt
        And the variable should be substituted
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step

        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()
        result = execute_demo_step(prompt_text="Show me information about file test_demo.md")

        assert result["executed_prompt"] == "Show me information about file test_demo.md"
        assert "[FILENAME]" not in result["executed_prompt"]

    def test_no_execution_without_confirmation(self):
        """
        Given a prompt is presented for confirmation
        When I do not confirm or execute
        Then the prompt should remain unexecuted
        And the system should continue waiting for confirmation
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, get_demo_state

        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()
        state = get_demo_state()
        assert state["executed_count"] == 0
        # No call to execute_demo_step, so nothing should be executed

    def test_conversational_sequence_full_demo(self):
        """
        Given a demo with multiple prompts
        When I step through the demo, confirming each prompt
        Then each prompt should be presented, confirmed, and executed in order
        And the demo should complete after the last prompt
        """
        from demo_assistant_mcp import load_demo_script, next_demo_step, execute_demo_step, get_demo_state

        load_demo_script("tests/fixtures/test_demo.md")
        for i in range(4):
            result = next_demo_step()
            assert result["status"] == "awaiting_confirmation"
            exec_result = execute_demo_step()
            assert exec_result["executed"] is True
        state = get_demo_state()
        assert state["executed_count"] == 4
        assert state["prompts_remaining"] == 0
        assert state["is_complete"] is True
