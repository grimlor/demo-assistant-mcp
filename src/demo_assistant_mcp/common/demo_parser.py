"""
Markdown parser for demo scripts

Extracts prompts and metadata from demo markdown files following the format:
    ### 💬 COPILOT CHAT PROMPT:
    ```
    Prompt text here with optional [VARIABLES]
    ```
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .error_handling import DemoError, ErrorType


@dataclass
class DemoPrompt:
    """Represents a single prompt extracted from a demo script"""

    text: str
    step_number: int
    section_title: str = ""
    variables: set[str] = field(default_factory=set[str])

    def __post_init__(self) -> None:
        """Detect variables in prompt text if none were provided."""
        if not self.variables:
            # Detect variables in the format [VARIABLE_NAME], keep the brackets
            self.variables = set(re.findall(r"\[[A-Z_]+\]", self.text))

    @property
    def has_variables(self) -> bool:
        """Check if this prompt contains any variables"""
        return len(self.variables) > 0


def parse_demo_markdown(file_path: str) -> list[DemoPrompt]:
    """
    Parse a demo markdown file and extract all prompts.

    Args:
        file_path: Path to the markdown file

    Returns:
        List of DemoPrompt objects in order

    Raises:
        DemoError: If file not found, invalid format, or no prompts found
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        raise DemoError.file_not_found(file_path)

    # Read file contents
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise DemoError(
            error=f"Failed to read demo file: {e}",
            error_type=ErrorType.INTERNAL,
            service="demo-assistant",
            suggestion="Ensure the file is readable and properly encoded",
        ) from e

    # Extract prompts
    prompts = _extract_prompts(content, file_path)

    if not prompts:
        raise DemoError.empty_demo(file_path)

    return prompts


def _extract_prompts(content: str, file_path: str) -> list[DemoPrompt]:
    """
    Extract all prompt blocks from markdown content.

    Args:
        content: The markdown file content
        file_path: Path to the file (for error messages)

    Returns:
        List of DemoPrompt objects
    """
    prompts: list[DemoPrompt] = []

    # Pattern to match prompt headers
    # Matches: ### 💬 COPILOT CHAT PROMPT:
    prompt_header_pattern = r"###\s*💬\s*COPILOT CHAT PROMPT:"

    # Find all prompt headers
    header_matches = list(re.finditer(prompt_header_pattern, content))

    if not header_matches:
        return []

    # Extract current section title (the ## heading before this prompt)
    def get_section_title(position: int) -> str:
        """Extract the section title (## heading) before this position"""
        before_text = content[:position]
        section_match = re.findall(r"^##\s+(.+)$", before_text, re.MULTILINE)
        return section_match[-1].strip() if section_match else ""

    # For each header, extract the code block that follows
    for i, match in enumerate(header_matches):
        header_end = match.end()

        # Get content between this header and the next (or end of file)
        if i < len(header_matches) - 1:
            next_header_start = header_matches[i + 1].start()
            section_content = content[header_end:next_header_start]
        else:
            section_content = content[header_end:]

        # Check that code block immediately follows (after whitespace)
        stripped_section = section_content.lstrip()
        if not stripped_section.startswith("```"):
            raise DemoError.invalid_format(
                file_path, f"prompt {i + 1} is missing code block markers"
            )

        # Look for code block in this section
        code_block_pattern = r"```\s*\n(.*?)```"
        code_match = re.search(code_block_pattern, section_content, re.DOTALL)

        if not code_match:
            raise DemoError.invalid_format(file_path, f"prompt {i + 1} has malformed code block")

        prompt_text = code_match.group(1).strip()
        section_title = get_section_title(match.start())

        prompt = DemoPrompt(text=prompt_text, step_number=i + 1, section_title=section_title)

        prompts.append(prompt)

    return prompts
