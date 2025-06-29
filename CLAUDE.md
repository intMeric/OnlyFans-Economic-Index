# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses UV for dependency management and a comprehensive Makefile for development tasks:

```bash
# Environment setup
make dev              # Install development dependencies
make install          # Install production dependencies only

# Testing and quality
make test             # Run tests with coverage (generates htmlcov/ reports)
make test-quick       # Run tests without coverage for faster feedback
make lint             # Check code with ruff
make lint-fix         # Auto-fix linting issues
make type-check       # Run mypy type checking
make format           # Format code with black
make check            # Run all quality checks (lint + type-check + format-check)

# Development workflow
make run              # Execute the application via entry point
make clean            # Remove build artifacts and cache files
make all              # Complete setup + all checks + tests

# Package management
make build            # Build distributable package
```

**Single Test Execution:**
```bash
python -m pytest tests/test_main.py::test_hello_default -v
```

## Project Architecture

### Package Structure
- **Main Package:** `src/onlyfans_economic_index/` - Core implementation
- **Entry Point:** CLI command `oei` maps to `onlyfans_economic_index.main:main`
- **Module Pattern:** Standard Python package with `__init__.py` and functional modules

### Development Stack
- **Build System:** Hatchling with UV package manager
- **Python Version:** 3.12+ requirement across all tools
- **Quality Tools:** Black (88 chars), Ruff (comprehensive rules), MyPy (strict)
- **Testing:** pytest with coverage reporting to both terminal and HTML

### Configuration Centralization
All development tools are configured in `pyproject.toml` with consistent:
- Python 3.12 targeting
- 88-character line length
- Strict type checking and comprehensive linting rules
- Test path configuration with source path mapping

### Key Files
- `pyproject.toml` - Complete project configuration and metadata
- `uv.lock` - Locked dependencies for reproducible builds
- `Makefile` - Development workflow automation (French documentation)
- `tests/test_main.py` - Test suite covering core functionality

## Development Notes

**Dependencies:** Always use `uv sync` (via `make dev`) rather than pip for dependency management.

**Code Quality:** The project enforces strict quality standards - all commits should pass `make check` before submission.

**Testing Strategy:** The project uses pytest with coverage reporting. Current implementation covers basic functionality with room for expanding test coverage of interactive features.

**CLI Application:** The project is designed as a command-line tool with the main entry point accessible via the `oei` command after installation.

## Code Guidelines

- **Code Comments:** All code comments must be written in English.