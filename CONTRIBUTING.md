# Contributing to Demo Assistant MCP Server

Thanks for your interest in contributing! This guide covers development setup, code style, and the pull request process.

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Getting Started

```bash
# Clone the repository
git clone https://github.com/grimlor/demo-assistant-mcp.git
cd demo-assistant-mcp

# Install all dependencies including dev extras
uv sync --all-extras
```

### Running Quality Checks

```bash
uv run task test                 # Run tests
uv run task cov                  # Run tests with coverage
uv run task lint                 # Lint (with auto-fix)
uv run task format               # Format code
uv run task type                 # Type check
uv run task check                # lint + type + test (all-in-one)
```

> **Note:** `uv run` is optional when the venv is activated via direnv.

All checks must pass before submitting a pull request.

## Code Style

- **Linting**: [Ruff](https://docs.astral.sh/ruff/) with rules E, W, F, I, N, UP, B, SIM, TCH, RUF, PLC0415, PLC2701
- **Line length**: 99 characters max
- **Type hints**: Required on all functions — pyright handles type checking
- **`from __future__ import annotations`**: Required in every Python file
- **Naming**: Follow PEP 8 conventions
- **Assertions**: Every `assert` must include a diagnostic message — bare assertions are prohibited

## Project Structure

```
src/demo_assistant_mcp/
├── server.py                  # MCP server entry point
├── common/
│   ├── demo_parser.py         # Demo script parser
│   ├── demo_state.py          # State management
│   ├── error_handling.py      # ActionableError
│   └── logging.py             # Logging configuration
└── tools/
    └── demo_tools.py          # Tool implementations
```

## Writing Tests

This project follows **Behavior-Driven Development (BDD)** rigorously. Tests are not an afterthought — they are the specification.

### BDD Principles

#### 1. Test Who/What/Why, Not How

Specifications describe **behavioral contracts**, not implementation details.

#### 2. Mock I/O Boundaries Only

**Mock at I/O boundaries:** file system reads, external services, network calls.

**Never mock:** internal helper functions, class methods within the module under test, or pure computation logic.

#### 3. 100% Coverage = Complete Specification

If we don't have 100% test coverage, we have an incomplete specification.

#### 4. Test Public APIs Only

Specifications exercise **only public APIs**. Private/internal functions (`_method`) achieve coverage through public API tests.

### Test Organization

Tests are organized by **consumer requirement** — each class covers a specific behavioral concern:

- Place tests in `tests/` with the `test_` prefix
- Group related tests in classes named `Test<RequirementBehavior>`
- Use fixtures from `tests/conftest.py` where possible

### Three-Part Contract

Every test requires all three:

1. **Class-level docstring** — REQUIREMENT / WHO / WHAT / WHY / MOCK BOUNDARY
2. **Method-level docstring** — Given / When / Then scenario
3. **Body comments** — `# Given:`, `# When:`, `# Then:` delineating the three phases

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`
2. **Make your changes** with clear, focused commits
3. **Run all checks** — tests, ruff, pyright must pass
4. **Submit a PR** with a clear description of what and why
5. **Respond to feedback** — maintainers may request changes

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` — New features
- `fix:` — Bug fixes
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `refactor:` — Code restructuring without behavior change

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Include a clear description of expected vs. actual behavior

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
