"""
BDD specification for the FastMCP server async tool wrappers.

Each ``@mcp.tool()`` coroutine in ``server.py`` is a thin async wrapper
that delegates to the synchronous business logic in ``demo_tools`` and
converts any ``ActionableError`` into a ``ToolResult.fail`` dict.

This module tests every wrapper's happy path and error path to ensure
full coverage of server.py.
Spec classes:
    TestLoadDemoScriptTool
    TestNextDemoStepTool
    TestExecuteDemoStepTool
    TestResetDemoTool
    TestGetDemoStateTool
    TestServerEntry
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from demo_assistant_mcp import server
from demo_assistant_mcp.common.error_handling import DemoError, DemoErrorType
from demo_assistant_mcp.server import (
    execute_demo_step_tool,
    get_demo_state_tool,
    load_demo_script_tool,
    next_demo_step_tool,
    reset_demo_tool,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TOOLS_PREFIX = "demo_assistant_mcp.server"

_DUMMY_RESULT: dict[str, Any] = {"success": True, "detail": "ok"}


def _make_demo_error(message: str = "boom") -> DemoError:
    """Create a real DemoError instance for testing the error path."""
    return DemoError(
        error=message,
        error_type=DemoErrorType.NO_DEMO_LOADED,
        service="demo-assistant",
        suggestion="Load a demo first",
    )


# ---------------------------------------------------------------------------
# TestLoadDemoScriptTool
# ---------------------------------------------------------------------------
class TestLoadDemoScriptTool:
    """
    REQUIREMENT: load_demo_script_tool delegates and wraps errors.

    WHO: MCP client calling the ``load_demo_script`` tool
    WHAT: The async wrapper calls the sync function and returns a string;
          on ActionableError it returns a serialised ToolResult.fail dict
    WHY: The MCP protocol requires string responses — the wrapper must
         serialise results and translate domain errors into structured
         failure dicts rather than propagating exceptions

    MOCK BOUNDARY:
        Mock:  demo_assistant_mcp.server.load_demo_script (sync function)
        Real:  load_demo_script_tool (async wrapper), ToolResult.fail
        Never: Mock ToolResult or the logging layer
    """

    @pytest.mark.asyncio
    async def test_happy_path_returns_stringified_result(self) -> None:
        """
        Given the underlying load_demo_script returns a result dict
        When load_demo_script_tool is awaited
        Then the result is returned as a string
        """
        # Given: sync function returns a result dict
        with patch(f"{_TOOLS_PREFIX}.load_demo_script", return_value=_DUMMY_RESULT):
            # When: the async wrapper is called
            result = await load_demo_script_tool("/path/to/demo.md")

        # Then: it returns the stringified result
        assert result == str(_DUMMY_RESULT), f"Expected stringified result dict, got {result!r}"

    @pytest.mark.asyncio
    async def test_error_path_returns_tool_result_fail(self) -> None:
        """
        Given the underlying load_demo_script raises an ActionableError
        When load_demo_script_tool is awaited
        Then a ToolResult.fail dict string is returned
        """
        # Given: sync function raises
        error = _make_demo_error("file not found")
        with patch(f"{_TOOLS_PREFIX}.load_demo_script", side_effect=error):
            # When: the async wrapper is called
            result = await load_demo_script_tool("/bad/path.md")

        # Then: result contains failure information
        assert "file not found" in result.lower(), (
            f"Expected error message in result, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TestNextDemoStepTool
# ---------------------------------------------------------------------------
class TestNextDemoStepTool:
    """
    REQUIREMENT: next_demo_step_tool delegates and wraps errors.

    WHO: MCP client calling the ``next_demo_step`` tool
    WHAT: The async wrapper calls next_demo_step and returns a string;
          on ActionableError it returns a ToolResult.fail dict
    WHY: Same serialisation and error-wrapping contract as load tool

    MOCK BOUNDARY:
        Mock:  demo_assistant_mcp.server.next_demo_step
        Real:  next_demo_step_tool, ToolResult.fail
        Never: Mock ToolResult or the logging layer
    """

    @pytest.mark.asyncio
    async def test_happy_path_returns_stringified_result(self) -> None:
        """
        Given next_demo_step returns a result dict
        When next_demo_step_tool is awaited
        Then the result string is returned
        """
        # Given: sync function returns a result dict
        with patch(f"{_TOOLS_PREFIX}.next_demo_step", return_value=_DUMMY_RESULT):
            # When: the async wrapper is called
            result = await next_demo_step_tool()

        # Then: it returns the stringified result
        assert result == str(_DUMMY_RESULT), f"Expected stringified result, got {result!r}"

    @pytest.mark.asyncio
    async def test_error_path_returns_tool_result_fail(self) -> None:
        """
        Given next_demo_step raises an ActionableError
        When next_demo_step_tool is awaited
        Then a ToolResult.fail dict string is returned
        """
        # Given: sync function raises an ActionableError
        error = _make_demo_error("no demo loaded")
        with patch(f"{_TOOLS_PREFIX}.next_demo_step", side_effect=error):
            # When: the async wrapper is called
            result = await next_demo_step_tool()

        # Then: result contains failure information
        assert "no demo loaded" in result.lower(), (
            f"Expected error message in result, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TestExecuteDemoStepTool
# ---------------------------------------------------------------------------
class TestExecuteDemoStepTool:
    """
    REQUIREMENT: execute_demo_step_tool delegates and wraps errors.

    WHO: MCP client calling the ``execute_demo_step`` tool
    WHAT: The async wrapper calls execute_demo_step (with optional
          prompt_text) and returns a string; on ActionableError it
          returns a ToolResult.fail dict
    WHY: Same serialisation and error-wrapping contract as load tool

    MOCK BOUNDARY:
        Mock:  demo_assistant_mcp.server.execute_demo_step
        Real:  execute_demo_step_tool, ToolResult.fail
        Never: Mock ToolResult or the logging layer
    """

    @pytest.mark.asyncio
    async def test_happy_path_returns_stringified_result(self) -> None:
        """
        Given execute_demo_step returns a result dict
        When execute_demo_step_tool is awaited with prompt_text
        Then the result string is returned
        """
        # Given: sync function returns a result dict
        with patch(f"{_TOOLS_PREFIX}.execute_demo_step", return_value=_DUMMY_RESULT):
            # When: the async wrapper is called with prompt_text
            result = await execute_demo_step_tool("Do something")

        # Then: it returns the stringified result
        assert result == str(_DUMMY_RESULT), f"Expected stringified result, got {result!r}"

    @pytest.mark.asyncio
    async def test_error_path_returns_tool_result_fail(self) -> None:
        """
        Given execute_demo_step raises an ActionableError
        When execute_demo_step_tool is awaited
        Then a ToolResult.fail dict string is returned
        """
        # Given: sync function raises an ActionableError
        error = _make_demo_error("execution failed")
        with patch(f"{_TOOLS_PREFIX}.execute_demo_step", side_effect=error):
            # When: the async wrapper is called
            result = await execute_demo_step_tool()

        # Then: result contains failure information
        assert "execution failed" in result.lower(), (
            f"Expected error message in result, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TestResetDemoTool
# ---------------------------------------------------------------------------
class TestResetDemoTool:
    """
    REQUIREMENT: reset_demo_tool delegates and wraps errors.

    WHO: MCP client calling the ``reset_demo`` tool
    WHAT: The async wrapper calls reset_demo and returns a string;
          on ActionableError it returns a ToolResult.fail dict
    WHY: Same serialisation and error-wrapping contract as load tool

    MOCK BOUNDARY:
        Mock:  demo_assistant_mcp.server.reset_demo
        Real:  reset_demo_tool, ToolResult.fail
        Never: Mock ToolResult or the logging layer
    """

    @pytest.mark.asyncio
    async def test_happy_path_returns_stringified_result(self) -> None:
        """
        Given reset_demo returns a result dict
        When reset_demo_tool is awaited
        Then the result string is returned
        """
        # Given: sync function returns a result dict
        with patch(f"{_TOOLS_PREFIX}.reset_demo", return_value=_DUMMY_RESULT):
            # When: the async wrapper is called
            result = await reset_demo_tool()

        # Then: it returns the stringified result
        assert result == str(_DUMMY_RESULT), f"Expected stringified result, got {result!r}"

    @pytest.mark.asyncio
    async def test_error_path_returns_tool_result_fail(self) -> None:
        """
        Given reset_demo raises an ActionableError
        When reset_demo_tool is awaited
        Then a ToolResult.fail dict string is returned
        """
        # Given: sync function raises an ActionableError
        error = _make_demo_error("reset failed")
        with patch(f"{_TOOLS_PREFIX}.reset_demo", side_effect=error):
            # When: the async wrapper is called
            result = await reset_demo_tool()

        # Then: result contains failure information
        assert "reset failed" in result.lower(), (
            f"Expected error message in result, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TestGetDemoStateTool
# ---------------------------------------------------------------------------
class TestGetDemoStateTool:
    """
    REQUIREMENT: get_demo_state_tool delegates and wraps errors.

    WHO: MCP client calling the ``get_demo_state`` tool
    WHAT: The async wrapper calls get_demo_state and returns a string;
          on ActionableError it returns a ToolResult.fail dict
    WHY: Same serialisation and error-wrapping contract as load tool

    MOCK BOUNDARY:
        Mock:  demo_assistant_mcp.server.get_demo_state
        Real:  get_demo_state_tool, ToolResult.fail
        Never: Mock ToolResult or the logging layer
    """

    @pytest.mark.asyncio
    async def test_happy_path_returns_stringified_result(self) -> None:
        """
        Given get_demo_state returns a result dict
        When get_demo_state_tool is awaited
        Then the result string is returned
        """
        # Given: sync function returns a result dict
        with patch(f"{_TOOLS_PREFIX}.get_demo_state", return_value=_DUMMY_RESULT):
            # When: the async wrapper is called
            result = await get_demo_state_tool()

        # Then: it returns the stringified result
        assert result == str(_DUMMY_RESULT), f"Expected stringified result, got {result!r}"

    @pytest.mark.asyncio
    async def test_error_path_returns_tool_result_fail(self) -> None:
        """
        Given get_demo_state raises an ActionableError
        When get_demo_state_tool is awaited
        Then a ToolResult.fail dict string is returned
        """
        # Given: sync function raises an ActionableError
        error = _make_demo_error("state check failed")
        with patch(f"{_TOOLS_PREFIX}.get_demo_state", side_effect=error):
            # When: the async wrapper is called
            result = await get_demo_state_tool()

        # Then: result contains failure information
        assert "state check failed" in result.lower(), (
            f"Expected error message in result, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TestServerEntry
# ---------------------------------------------------------------------------
class TestServerEntry:
    """
    REQUIREMENT: The server must start via run() using stdio transport.

    WHO: Package consumers using uvx or python -m
    WHAT: run() calls mcp.run(transport="stdio")
    WHY: The entry point is the public contract for starting the server —
         changing it breaks existing MCP client configurations

    MOCK BOUNDARY:
        Mock:  FastMCP.run() (3rd-party — we don't want to actually start
               stdio transport in tests)
        Real:  Our run() function
        Never: Our own wrapper logic around the entry point
    """

    def test_run_invokes_fastmcp_run_with_stdio(self) -> None:
        """
        Given the server module
        When run() is called
        Then FastMCP.run(transport="stdio") is invoked
        """
        # Given: the FastMCP instance
        mcp_instance = getattr(server, "mcp", None)
        assert mcp_instance is not None, "server module should export 'mcp' FastMCP instance"

        # When: calling run() with mocked FastMCP.run
        with patch.object(mcp_instance, "run") as mock_run:
            server.run()

        # Then: FastMCP.run called with stdio transport
        mock_run.assert_called_once_with(transport="stdio")
