"""
BDD specification for conversational orchestration workflow.

Covers the following requirement class:
- TestConversationalOrchestration — confirmation-gated prompt execution using
  real fixture files for integration-level confidence
"""

from __future__ import annotations

from demo_assistant_mcp import (
    execute_demo_step,
    get_demo_state,
    load_demo_script,
    next_demo_step,
)


class TestConversationalOrchestration:
    """
    REQUIREMENT: Prompts follow a present-confirm-execute conversational flow.

    WHO: Presenter interacting with the MCP assistant during a live demo
    WHAT: next_demo_step presents a prompt in awaiting_confirmation state
          with zero executed count; execute_demo_step runs the prompt and
          advances; custom prompt_text substitutes variables; omitting
          execute_demo_step leaves the prompt unexecuted; stepping through
          all prompts completes the demo with is_complete=True
    WHY: The assistant must never auto-execute — the presenter controls
         pacing and can modify prompts to match the live context

    MOCK BOUNDARY:
        Mock:  nothing — uses real fixture file tests/fixtures/test_demo.md
        Real:  load_demo_script (filesystem read), next_demo_step, execute_demo_step,
               get_demo_state
        Never: Mock the file system — these tests use real fixtures for integration confidence
    """

    def test_prompt_presented_and_waits_for_confirmation(self) -> None:
        """
        Given a loaded demo script
        When I advance to the next prompt
        Then the prompt is presented in awaiting_confirmation state with zero executions
        """
        # Given: a demo loaded from the real fixture file
        load_demo_script("tests/fixtures/test_demo.md")

        # When: the presenter advances to the first prompt
        result = next_demo_step()

        # Then: prompt is presented but not executed
        assert result["prompt_text"] == "What is the current date and time?", (
            f"Expected first fixture prompt text, got {result['prompt_text']!r}"
        )
        assert result["status"] == "awaiting_confirmation", (
            f"Expected 'awaiting_confirmation' status, got {result['status']!r}"
        )
        state = get_demo_state()
        assert state["executed_count"] == 0, (
            f"Expected 0 executions before confirmation, got {state['executed_count']}"
        )

    def test_prompt_executed_only_after_confirmation(self) -> None:
        """
        Given a prompt is awaiting confirmation
        When I confirm execution
        Then the prompt is executed and the executed count advances
        """
        # Given: a demo loaded with the first prompt awaiting confirmation
        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()

        # When: the presenter confirms execution
        result = execute_demo_step()

        # Then: step 1 is complete and state reflects the execution
        assert result["executed"] is True, f"Expected executed=True, got {result.get('executed')}"
        assert result["step_completed"] == 1, (
            f"Expected step_completed=1, got {result.get('step_completed')}"
        )
        state = get_demo_state()
        assert state["executed_count"] == 1, (
            f"Expected executed_count=1 after one confirmation, got {state['executed_count']}"
        )

    def test_user_can_modify_prompt_before_execution(self) -> None:
        """
        Given a prompt awaiting confirmation
        When I provide modified prompt text and confirm
        Then the modified text is executed with variables substituted
        """
        # Given: a demo loaded with the first prompt awaiting confirmation
        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()

        # When: the presenter provides custom text with substituted variables
        result = execute_demo_step(prompt_text="Show me information about file test_demo.md")

        # Then: the custom text is used as the executed prompt
        assert result["executed_prompt"] == "Show me information about file test_demo.md", (
            f"Expected custom prompt text, got {result['executed_prompt']!r}"
        )
        assert "[FILENAME]" not in result["executed_prompt"], (
            f"Variable [FILENAME] should not appear in executed prompt, "
            f"got {result['executed_prompt']!r}"
        )

    def test_no_execution_without_confirmation(self) -> None:
        """
        Given a prompt is presented for confirmation
        When no execute call is made
        Then the executed count remains zero
        """
        # Given: a demo loaded with the first prompt presented
        load_demo_script("tests/fixtures/test_demo.md")
        next_demo_step()

        # When: no execute_demo_step call is made

        # Then: nothing has been executed
        state = get_demo_state()
        assert state["executed_count"] == 0, (
            f"Expected 0 executions without confirmation, got {state['executed_count']}"
        )

    def test_conversational_sequence_full_demo(self) -> None:
        """
        Given a demo with multiple prompts
        When I step through confirming each prompt
        Then each prompt is presented, confirmed, and executed in order
        And the demo completes after the last prompt
        """
        # Given: a demo loaded from the fixture file
        load_demo_script("tests/fixtures/test_demo.md")

        # When: the presenter steps through every prompt
        for i in range(4):
            result = next_demo_step()
            assert result["status"] == "awaiting_confirmation", (
                f"Step {i + 1}: expected 'awaiting_confirmation', got {result['status']!r}"
            )
            exec_result = execute_demo_step()
            assert exec_result["executed"] is True, (
                f"Step {i + 1}: expected executed=True, got {exec_result.get('executed')}"
            )

        # Then: the demo is fully complete
        state = get_demo_state()
        assert state["executed_count"] == 4, (
            f"Expected 4 total executions, got {state['executed_count']}"
        )
        assert state["prompts_remaining"] == 0, (
            f"Expected 0 prompts remaining, got {state['prompts_remaining']}"
        )
        assert state["is_complete"] is True, (
            f"Expected is_complete=True after all prompts, got {state.get('is_complete')}"
        )
