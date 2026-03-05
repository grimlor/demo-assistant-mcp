"""
BDD specification for demo-assistant-mcp core functionality.

Covers the following requirement classes:
- TestLoadingDemoScripts — loading, parsing, and file-read failure modes
- TestVariableHandling — variable detection, substitution via prompt_text and state dict
- TestSequentialExecution — step-through execution, confirmation gate, and fallback paths
- TestDemoStateManagement — state tracking, reset, boundary access, and misuse guards
- TestErrorRecovery — actionable error messages with recovery guidance
- TestMCPIntegration — tool function signatures and discoverability
"""

from __future__ import annotations

import inspect
import typing
from typing import Any
from unittest.mock import patch

import pytest

from demo_assistant_mcp import (
    ActionableError,
    DemoError,
    execute_demo_step,
    get_demo_state,
    get_state,
    load_demo_script,
    next_demo_step,
    parse_demo_markdown,
    reset_demo,
)


class TestLoadingDemoScripts:
    """
    REQUIREMENT: Demo scripts load from markdown and expose executable prompts.

    WHO: Technical presenter starting a demo session
    WHAT: Valid markdown files produce an ordered prompt list with count and
          first-prompt preview; missing files raise NOT_FOUND with path guidance;
          empty files raise EMPTY_DEMO identifying the absence of prompts;
          malformed files raise VALIDATION identifying format issues;
          unreadable files (permission denied) raise INTERNAL with OS message;
          unterminated code blocks raise VALIDATION identifying the malformed prompt
    WHY: Loading is the entry point for every demo — silent failures or
         cryptic errors here derail the entire presentation

    MOCK BOUNDARY:
        Mock:  pathlib.Path.exists / read_text via mock_file_system fixture (filesystem I/O)
        Real:  load_demo_script, parse_demo_markdown, DemoError factory methods
        Never: Construct load result dicts directly — always obtain via load_demo_script()
    """

    def test_load_valid_demo_returns_prompt_count(self, mock_file_system: None) -> None:
        """
        Given a valid demo markdown file with 3 prompts
        When I load the demo script
        Then I should receive confirmation with prompt count
        And the first prompt should be presented for confirmation
        """
        # Given: a valid demo file (provided by mock_file_system fixture)

        # When: the presenter loads the demo script
        result = load_demo_script("/path/to/demo.md")

        # Then: success with correct prompt count and first prompt details
        assert result["success"] is True, (
            f"Expected successful load, got success={result.get('success')}"
        )
        assert result["prompt_count"] == 3, (
            f"Expected 3 prompts from valid demo, got {result.get('prompt_count')}"
        )
        assert "first_prompt" in result, (
            f"Expected 'first_prompt' key in result, got keys: {list(result.keys())}"
        )
        assert result["first_prompt"]["text"] == "What repository am I working in?", (
            f"Expected first prompt 'What repository am I working in?', "
            f"got {result['first_prompt']['text']!r}"
        )
        assert result["first_prompt"]["step_number"] == 1, (
            f"Expected step_number=1, got {result['first_prompt']['step_number']}"
        )

    def test_load_demo_with_file_not_found(self) -> None:
        """
        Given a demo file path that doesn't exist
        When I attempt to load the demo
        Then I should receive an ActionableError with recovery suggestion
        """
        # Given: a file path that does not exist on disk
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the presenter attempts to load the demo
            load_demo_script("/nonexistent/demo.md")

        # Then: error identifies the problem and suggests a fix
        assert "not found" in str(exc_info.value).lower(), (
            f"Expected 'not found' in error message, got: {exc_info.value}"
        )
        assert exc_info.value.suggestion is not None, (
            "Expected a recovery suggestion on file-not-found error"
        )
        assert "check" in exc_info.value.suggestion.lower(), (
            f"Expected suggestion to mention 'check', got: {exc_info.value.suggestion!r}"
        )

    def test_load_empty_demo_fails_gracefully(self, empty_demo_markdown: str) -> None:
        """
        Given a markdown file with no executable prompts
        When I load the demo
        Then I should receive an ActionableError explaining no prompts were found
        """
        # Given: a markdown file containing no prompt blocks
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=empty_demo_markdown),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the presenter loads the empty file
            load_demo_script("/path/to/empty.md")

        # Then: error clearly states no prompts were found
        assert "no prompts" in str(exc_info.value).lower(), (
            f"Expected 'no prompts' in error message, got: {exc_info.value}"
        )

    def test_load_malformed_demo_identifies_issues(self, malformed_demo_markdown: str) -> None:
        """
        Given a markdown file with malformed prompt blocks
        When I load the demo
        Then I should receive an ActionableError identifying format issues
        """
        # Given: a markdown file with broken prompt formatting
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=malformed_demo_markdown),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the presenter loads the malformed file
            load_demo_script("/path/to/malformed.md")

        # Then: error identifies the formatting problem
        error_msg = str(exc_info.value).lower()
        assert "format" in error_msg or "invalid" in error_msg, (
            f"Expected 'format' or 'invalid' in error message, got: {exc_info.value}"
        )

    def test_permission_denied_produces_internal_error(self) -> None:
        """
        Given a file that exists but raises PermissionError on read
        When parse_demo_markdown is called
        Then a DemoError with INTERNAL type is raised containing the OS message
        """
        # Given: a file that exists but is unreadable
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", side_effect=PermissionError("Permission denied")),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the parser tries to read it
            parse_demo_markdown("/protected/demo.md")

        # Then: the error wraps the OS message and suggests a fix
        assert "Permission denied" in str(exc_info.value), (
            f"Expected OS error in message, got: {exc_info.value}"
        )
        assert exc_info.value.suggestion is not None, (
            "Expected a recovery suggestion for read errors"
        )
        assert "readable" in exc_info.value.suggestion.lower(), (
            f"Expected suggestion about readability, got: {exc_info.value.suggestion!r}"
        )

    def test_unterminated_code_block_raises_format_error(
        self, code_block_opens_but_never_closes: str
    ) -> None:
        """
        Given a demo file where a code block opens but never closes
        When parse_demo_markdown is called
        Then a DemoError identifying the malformed prompt is raised
        """
        # Given: a file with an unterminated code block
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=code_block_opens_but_never_closes),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the parser processes the file
            parse_demo_markdown("/path/to/broken.md")

        # Then: error identifies the malformed prompt
        error_msg = str(exc_info.value).lower()
        assert "malformed" in error_msg or "code block" in error_msg, (
            f"Expected 'malformed' or 'code block' in error, got: {exc_info.value}"
        )


class TestVariableHandling:
    """
    REQUIREMENT: Prompts support placeholder variables that are detected and substitutable.

    WHO: Presenter working with dynamic data (PR IDs, branch names, filenames)
    WHAT: Variables in [BRACKET] syntax are detected and reported when a prompt
          is presented; executing with custom prompt_text substitutes values;
          executing without substitution preserves the original prompt text;
          pre-registered variable_substitutions in state are applied on execute
    WHY: Demo data changes between sessions — hardcoded values force manual
         editing of demo scripts before every presentation

    MOCK BOUNDARY:
        Mock:  pathlib.Path.exists / read_text via mock_file_system or loaded_demo_with_variables fixture
        Real:  load_demo_script, next_demo_step, execute_demo_step, variable detection
        Never: Manipulate DemoState.pending_prompt directly
    """

    def test_detect_variables_in_prompt(self, mock_file_system: None) -> None:
        """
        Given a demo with prompts containing [PR_ID] and [BRANCH_NAME]
        When I advance to a prompt with variables
        Then variables should be detected and reported
        """
        # Given: a loaded demo with variable-containing prompts
        load_demo_script("/path/to/demo.md")
        next_demo_step()  # Present first prompt
        execute_demo_step()  # Execute first prompt to advance

        # When: the presenter advances to the prompt containing [PR_ID]
        result = next_demo_step()

        # Then: the variable is detected and listed
        assert result["has_variables"] is True, (
            f"Expected has_variables=True for prompt with [PR_ID], "
            f"got {result.get('has_variables')}"
        )
        assert "[PR_ID]" in result["variables"], (
            f"Expected [PR_ID] in variables list, got {result.get('variables')}"
        )

    def test_execute_prompt_with_variable_substitution(self, mock_file_system: None) -> None:
        """
        Given a prompt with [PR_ID] variable
        When I execute with substituted text
        Then the executed prompt should contain the substituted value
        """
        # Given: a demo loaded and advanced to the prompt with [PR_ID]
        load_demo_script("/path/to/demo.md")
        next_demo_step()

        # When: the presenter provides substituted prompt text
        result = execute_demo_step(prompt_text="Analyze PR 12345 and show me the comments")

        # Then: the executed prompt uses the substituted text
        assert result["executed_prompt"] == "Analyze PR 12345 and show me the comments", (
            f"Expected substituted prompt text, got {result['executed_prompt']!r}"
        )
        assert "[PR_ID]" not in result["executed_prompt"], (
            f"Variable [PR_ID] should be replaced, got {result['executed_prompt']!r}"
        )

    def test_execute_prompt_without_substitution_keeps_original(
        self, mock_file_system: None
    ) -> None:
        """
        Given a prompt without variables
        When I execute without modification
        Then the original prompt text should be executed
        """
        # Given: a demo loaded at the first prompt (no variables)
        load_demo_script("/path/to/demo.md")

        # When: the presenter executes without providing custom text
        result = execute_demo_step()

        # Then: the original prompt text is used
        assert result["executed_prompt"] == "What repository am I working in?", (
            f"Expected original prompt text, got {result['executed_prompt']!r}"
        )

    def test_variables_replaced_from_state_substitutions(
        self, loaded_demo_with_variables: None
    ) -> None:
        """
        Given a loaded demo with variable_substitutions {"PR_ID": "42", "BRANCH": "main"}
        When execute_demo_step is called without prompt_text
        Then [PR_ID] and [BRANCH] are replaced in the executed prompt
        """
        # Given: demo loaded with pre-registered substitutions (via fixture)

        # When: execute without providing custom text
        result = execute_demo_step()

        # Then: variables are substituted from state
        assert result["executed_prompt"] == "Analyze PR 42 on branch main", (
            f"Expected substituted text, got {result['executed_prompt']!r}"
        )
        assert "[PR_ID]" not in result["executed_prompt"], (
            "Variable [PR_ID] should have been substituted"
        )
        assert "[BRANCH]" not in result["executed_prompt"], (
            "Variable [BRANCH] should have been substituted"
        )


class TestSequentialExecution:
    """
    REQUIREMENT: Prompts execute one at a time with a confirmation gate between steps.

    WHO: Presenter stepping through a live demo
    WHAT: next_demo_step presents the prompt without executing it;
          execute_demo_step runs the current prompt and auto-presents the next;
          completing all prompts marks the demo done; calling next_demo_step
          after completion returns a 'demo_complete' status;
          executing without a pending prompt falls back to the current step;
          executing with no prompt available raises a DemoError with guidance
    WHY: Presenters need to discuss each step with the audience before
         execution — auto-running prompts would break the narrative flow

    MOCK BOUNDARY:
        Mock:  pathlib.Path.exists / read_text via mock_file_system fixture (filesystem I/O)
        Real:  load_demo_script, next_demo_step, execute_demo_step, get_demo_state, DemoState
        Never: Advance DemoState.current_step directly
    """

    def test_next_step_presents_prompt_without_executing(self, mock_file_system: None) -> None:
        """
        Given a loaded demo
        When I call next_demo_step
        Then the next prompt is presented in awaiting_confirmation status
        And the execution count remains zero
        """
        # Given: a demo loaded from a valid markdown file
        load_demo_script("/path/to/demo.md")

        # When: the presenter advances to the next prompt
        result = next_demo_step()

        # Then: prompt is presented but not executed
        assert result["prompt_text"] == "What repository am I working in?", (
            f"Expected first prompt text, got {result['prompt_text']!r}"
        )
        assert result["status"] == "awaiting_confirmation", (
            f"Expected 'awaiting_confirmation' status, got {result['status']!r}"
        )
        state = get_demo_state()
        assert state["executed_count"] == 0, (
            f"Expected 0 executed after next_step (no execution yet), "
            f"got {state['executed_count']}"
        )

    def test_execute_step_runs_current_prompt(self, mock_file_system: None) -> None:
        """
        Given a prompt awaiting confirmation
        When I call execute_demo_step
        Then the prompt is executed and the next prompt is presented
        """
        # Given: a demo loaded with the first prompt awaiting confirmation
        load_demo_script("/path/to/demo.md")
        next_demo_step()

        # When: the presenter confirms execution
        result = execute_demo_step()

        # Then: step 1 is executed and next prompt is auto-presented
        assert result["executed"] is True, (
            f"Expected executed=True after execute_demo_step, got {result.get('executed')}"
        )
        assert result["step_completed"] == 1, (
            f"Expected step_completed=1, got {result.get('step_completed')}"
        )
        assert "next_prompt" in result, (
            f"Expected 'next_prompt' key after execution, got keys: {list(result.keys())}"
        )
        assert result["next_prompt"]["text"] == "Analyze PR [PR_ID] and show me the comments", (
            f"Expected next prompt with [PR_ID], got {result['next_prompt']['text']!r}"
        )

    def test_complete_demo_sequence(self, mock_file_system: None) -> None:
        """
        Given a demo with 3 prompts
        When I execute all prompts in sequence
        Then the last execution marks the demo as complete
        """
        # Given: a demo loaded with 3 prompts
        load_demo_script("/path/to/demo.md")

        # When: the presenter steps through and executes all 3 prompts
        result: dict[str, Any] = {}
        for _i in range(3):
            next_demo_step()
            result = execute_demo_step()

        # Then: the final result indicates demo completion
        assert result["demo_complete"] is True, (
            f"Expected demo_complete=True after all 3 prompts, got {result.get('demo_complete')}"
        )
        assert result["total_steps"] == 3, (
            f"Expected total_steps=3, got {result.get('total_steps')}"
        )

    def test_next_step_after_completion_indicates_done(self, mock_file_system: None) -> None:
        """
        Given a completed demo
        When I call next_demo_step
        Then the status indicates the demo is complete with no more prompts
        """
        # Given: a demo that has been fully executed
        load_demo_script("/path/to/demo.md")
        for _i in range(3):
            next_demo_step()
            execute_demo_step()

        # When: the presenter tries to advance past the last prompt
        result = next_demo_step()

        # Then: status indicates completion
        assert result["status"] == "demo_complete", (
            f"Expected 'demo_complete' status after all prompts, got {result['status']!r}"
        )
        assert "no more prompts" in result["message"].lower(), (
            f"Expected 'no more prompts' in message, got {result['message']!r}"
        )

    def test_execute_without_pending_prompt_uses_current_step(self) -> None:
        """
        Given a loaded demo with no pending prompt (next_demo_step not called)
        When execute_demo_step is called without prompt_text
        Then the current step's prompt is executed as fallback
        """
        # Given: a demo loaded but next_demo_step not called (no pending_prompt)
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text",
                return_value=(
                    "# Demo\n\n### \U0001f4ac COPILOT CHAT PROMPT:\n```\nWhat time is it?\n```\n"
                ),
            ),
        ):
            load_demo_script("/path/to/demo.md")

        # When: execute is called without next_demo_step
        result = execute_demo_step()

        # Then: the first prompt is used as fallback
        assert result["executed"] is True, f"Expected executed=True, got {result.get('executed')}"
        assert result["executed_prompt"] == "What time is it?", (
            f"Expected fallback to current prompt text, got {result['executed_prompt']!r}"
        )

    def test_execute_with_no_prompt_available_raises_error(self) -> None:
        """
        Given a loaded demo where current_step is past the end and no pending prompt
        When execute_demo_step is called
        Then a DemoError instructs the presenter to call next_demo_step first
        """
        # Given: a completed demo with no pending prompt
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text",
                return_value=("# Demo\n\n### \U0001f4ac COPILOT CHAT PROMPT:\n```\nHello\n```\n"),
            ),
        ):
            load_demo_script("/path/to/demo.md")

        state = get_state()
        state.current_step = state.total_prompts  # past the end
        state.pending_prompt = None

        # When: execute is called with nothing available
        with pytest.raises(ActionableError) as exc_info:
            execute_demo_step()

        # Then: error suggests calling next_demo_step first
        assert (
            "next_demo_step" in str(exc_info.value).lower()
            or "no prompt" in str(exc_info.value).lower()
        ), f"Expected guidance about next_demo_step, got: {exc_info.value}"


class TestDemoStateManagement:
    """
    REQUIREMENT: Demo state is trackable, resettable, and guards against misuse.

    WHO: Presenter managing demo flow during a session
    WHAT: reset_demo returns state to the beginning with zero execution count;
          get_demo_state reports total prompts, executed count, current step,
          and remaining count; executing or advancing without a loaded demo
          raises an ActionableError instructing the presenter to load first;
          get_current_prompt returns None when current_step is past the end
    WHY: Presenters need to restart demos, check progress mid-session, and
         receive clear guidance when they skip the load step

    MOCK BOUNDARY:
        Mock:  pathlib.Path.exists / read_text via mock_file_system fixture (filesystem I/O)
        Real:  load_demo_script, next_demo_step, execute_demo_step, reset_demo, get_demo_state
        Never: Construct state dicts directly — always obtain via get_demo_state()
    """

    def test_reset_demo_returns_to_beginning(self, mock_file_system: None) -> None:
        """
        Given a demo in progress with some prompts executed
        When I call reset_demo
        Then the demo returns to step 0 with zero executions
        """
        # Given: a demo with one prompt executed and another presented
        load_demo_script("/path/to/demo.md")
        next_demo_step()
        execute_demo_step()
        next_demo_step()

        # When: the presenter resets the demo
        result = reset_demo()

        # Then: state is back to the beginning
        assert result["success"] is True, (
            f"Expected successful reset, got success={result.get('success')}"
        )
        assert result["current_step"] == 0, (
            f"Expected current_step=0 after reset, got {result.get('current_step')}"
        )
        assert result["executed_count"] == 0, (
            f"Expected executed_count=0 after reset, got {result.get('executed_count')}"
        )

    def test_get_demo_state_shows_progress(self, mock_file_system: None) -> None:
        """
        Given a demo with one prompt executed
        When I query the demo state
        Then I see accurate total, executed, current, and remaining counts
        """
        # Given: a demo with one prompt executed
        load_demo_script("/path/to/demo.md")
        next_demo_step()
        execute_demo_step()

        # When: the presenter checks state
        state = get_demo_state()

        # Then: all progress fields are accurate
        assert state["total_prompts"] == 3, (
            f"Expected total_prompts=3, got {state.get('total_prompts')}"
        )
        assert state["executed_count"] == 1, (
            f"Expected executed_count=1 after one execution, got {state.get('executed_count')}"
        )
        assert state["current_step"] == 1, (
            f"Expected current_step=1 after one execution, got {state.get('current_step')}"
        )
        assert state["prompts_remaining"] == 2, (
            f"Expected 2 prompts remaining, got {state.get('prompts_remaining')}"
        )

    def test_execute_without_loading_demo_fails(self) -> None:
        """
        Given no demo has been loaded
        When I attempt to execute a step
        Then an ActionableError instructs me to load a demo first
        """
        # Given: no demo loaded (clean state from autouse fixture)

        # When: the presenter tries to execute without loading
        with pytest.raises(ActionableError) as exc_info:
            execute_demo_step()

        # Then: error tells them to load a demo
        error_msg = str(exc_info.value).lower()
        assert "load" in error_msg, f"Expected 'load' in error message, got: {exc_info.value}"
        assert "demo" in error_msg, f"Expected 'demo' in error message, got: {exc_info.value}"

    def test_next_step_without_loading_demo_fails(self) -> None:
        """
        Given no demo has been loaded
        When I attempt to advance to next step
        Then an ActionableError is raised
        """
        # Given: no demo loaded (clean state from autouse fixture)

        # When: the presenter tries to advance without loading
        with pytest.raises(ActionableError) as exc_info:
            next_demo_step()

        # Then: error mentions loading
        assert "load" in str(exc_info.value).lower(), (
            f"Expected 'load' in error message, got: {exc_info.value}"
        )

    def test_get_current_prompt_returns_none_past_end(self) -> None:
        """
        Given a loaded demo where current_step equals total_prompts
        When get_current_prompt is called
        Then None is returned
        """
        # Given: a demo loaded and stepped past the last prompt
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text",
                return_value=("# Demo\n\n### \U0001f4ac COPILOT CHAT PROMPT:\n```\nHello\n```\n"),
            ),
        ):
            load_demo_script("/path/to/demo.md")

        state = get_state()
        state.current_step = state.total_prompts  # past the end

        # When: the state is queried for a prompt
        result = state.get_current_prompt()

        # Then: None is returned (no IndexError)
        assert result is None, f"Expected None for out-of-range step, got {result}"


class TestErrorRecovery:
    """
    REQUIREMENT: Errors include actionable guidance so presenters can self-recover.

    WHO: Presenter encountering issues during a live demo
    WHAT: DemoError instances carry a human-readable suggestion field;
          format errors include a context dict with an example of correct format
    WHY: Demos run under time pressure — vague errors force the presenter
         to abandon the demo; actionable errors let them fix and continue

    MOCK BOUNDARY:
        Mock:  pathlib.Path.exists / read_text (for load-path error tests)
        Real:  DemoError construction, ActionableError field access, load_demo_script error paths
        Never: Catch and re-raise errors — let pytest.raises verify them
    """

    def test_actionable_error_includes_suggestion(self) -> None:
        """
        When a DemoError is constructed with a suggestion
        Then the suggestion is accessible on the error instance
        """
        # Given: error details for a file-not-found scenario

        # When: a DemoError is constructed directly
        error = DemoError(
            error="Demo file not found at /path/to/demo.md",
            error_type="not_found",
            service="demo-assistant",
            suggestion="Check that the file path is correct and the file exists",
        )

        # Then: the error message and suggestion are accessible
        assert "not found" in str(error), f"Expected 'not found' in error string, got: {error}"
        assert error.suggestion == "Check that the file path is correct and the file exists", (
            f"Expected specific suggestion text, got: {error.suggestion!r}"
        )

    def test_invalid_prompt_format_gives_format_example(
        self, malformed_demo_markdown: str
    ) -> None:
        """
        Given a demo with invalid prompt format
        When I load the demo
        Then the error context includes an example of correct format
        """
        # Given: a markdown file with broken prompt formatting
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=malformed_demo_markdown),
            pytest.raises(ActionableError) as exc_info,
        ):
            # When: the presenter loads the malformed file
            load_demo_script("/path/to/demo.md")

        # Then: error context provides a correct format example
        assert exc_info.value.context is not None, (
            "Expected error context with format example, got None"
        )
        assert "### 💬 COPILOT CHAT PROMPT:" in exc_info.value.context["example"], (
            f"Expected format example with prompt header, "
            f"got: {exc_info.value.context.get('example')!r}"
        )


class TestMCPIntegration:
    """
    REQUIREMENT: Tool functions expose correct signatures for MCP discoverability.

    WHO: FastMCP server registering tool functions for Copilot
    WHAT: load_demo_script accepts a file_path: str parameter;
          next_demo_step has no required parameters;
          execute_demo_step accepts an optional prompt_text defaulting to None
    WHY: MCP tool registration relies on function signatures — incorrect
         signatures cause silent registration failures or runtime type errors

    MOCK BOUNDARY:
        Mock:  nothing — these tests inspect pure function metadata
        Real:  inspect.signature, typing.get_type_hints
        Never: Import private tool registration internals
    """

    def test_load_tool_accepts_file_path_parameter(self) -> None:
        """
        When the load_demo_script signature is inspected
        Then it accepts a file_path parameter of type str
        """
        # Given: the load_demo_script function

        # When: its signature is inspected
        sig = inspect.signature(load_demo_script)
        hints = typing.get_type_hints(load_demo_script)

        # Then: file_path parameter exists and is typed as str
        assert "file_path" in sig.parameters, (
            f"Expected 'file_path' parameter, got: {list(sig.parameters.keys())}"
        )
        assert hints["file_path"] is str, (
            f"Expected file_path type to be str, got {hints['file_path']}"
        )

    def test_next_step_tool_requires_no_parameters(self) -> None:
        """
        When the next_demo_step signature is inspected
        Then it has no required parameters
        """
        # Given: the next_demo_step function

        # When: its signature is inspected for required params
        sig = inspect.signature(next_demo_step)
        required_params = [
            p for p in sig.parameters.values() if p.default == inspect.Parameter.empty
        ]

        # Then: no parameters are required
        assert len(required_params) == 0, (
            f"Expected no required params, got {len(required_params)}: "
            f"{[p.name for p in required_params]}"
        )

    def test_execute_tool_accepts_optional_prompt_override(self) -> None:
        """
        When the execute_demo_step signature is inspected
        Then it accepts an optional prompt_text parameter defaulting to None
        """
        # Given: the execute_demo_step function

        # When: its signature is inspected
        sig = inspect.signature(execute_demo_step)

        # Then: prompt_text exists and defaults to None
        assert "prompt_text" in sig.parameters, (
            f"Expected 'prompt_text' parameter, got: {list(sig.parameters.keys())}"
        )
        assert sig.parameters["prompt_text"].default is None, (
            f"Expected prompt_text default to be None, "
            f"got {sig.parameters['prompt_text'].default!r}"
        )
