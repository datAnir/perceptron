# Arcon Development Guide

This document provides comprehensive guidance for developers working on Arcon.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Code Organization](#code-organization)
- [Testing Strategy](#testing-strategy)
- [Contributing Guidelines](#contributing-guidelines)
- [Release Process](#release-process)

## Architecture Overview

### System Design

Arcon follows a modular, layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer                             │
│  (arcon chat, arcon sessions, arcon config, etc.)       │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                 Agent Layer                              │
│  (CodingAssistant, Debugger, CodeReviewer, etc.)       │
│  + Skills System (domain knowledge injection)           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                Session Layer                             │
│  (Conversation state, message history, token tracking)  │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Provider Layer                             │
│  (Anthropic, OpenAI, Ollama abstractions)              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                 Tool Layer                               │
│  (File operations, bash execution, custom tools)        │
└─────────────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Storage Layer                              │
│  (SQLite persistence, session management)               │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Provider System

**Location**: `src/arcon/providers/`

**Purpose**: Abstract LLM integrations supporting multiple providers

**Key Files**:
- `interface.py`: `LLMProvider` abstract base class
- `anthropic.py`: Anthropic Claude integration
- `openai.py`: OpenAI GPT integration
- `ollama.py`: Local Ollama integration
- `resolver.py`: Provider factory with config loading

**Design Patterns**:
- Abstract Factory (ProviderResolver)
- Strategy Pattern (LLMProvider implementations)
- Async/Await for streaming responses

#### 2. Agent System

**Location**: `src/arcon/agents/`

**Purpose**: Specialized AI personas with domain expertise

**Key Files**:
- `base.py`: `Agent` abstract base class
- `loader.py`: YAML agent definition loading
- `registry.py`: Agent discovery and routing

**Agent Routing Priority**:
1. Explicit name mention in query
2. Context hints (file extension, language)
3. Keyword matching against agent tags

#### 3. Skills System

**Location**: `src/arcon/skills/`

**Purpose**: Reusable domain knowledge modules

**Key Files**:
- `base.py`: `Skill` data class
- `loader.py`: Markdown+YAML frontmatter parsing
- `registry.py`: Skill cataloging and search
- `manager.py`: Relevance-based skill selection

**Skill Format**:
```markdown
---
name: skill-name
description: Brief description
category: development
tags: ["tag1", "tag2"]
---

# Skill Content

Detailed knowledge, patterns, examples...
```

#### 4. Tool System

**Location**: `src/arcon/tools/`

**Purpose**: Executable functions for agents

**Key Files**:
- `base.py`: `Tool` abstract base class
- `builtin.py`: Built-in tools (file ops, bash)
- `registry.py`: Tool discovery and management
- `executor.py`: Tool execution with timeout/truncation

**Tool Execution Flow**:
1. Agent requests tool execution
2. Executor validates tool exists and parameters
3. Tool.execute() runs (with timeout)
4. Output truncated if > 10KB
5. ToolExecutionResult returned

#### 5. Storage System

**Location**: `src/arcon/storage/`

**Purpose**: SQLite persistence for sessions

**Key Files**:
- `models.py`: SQLAlchemy ORM models
- `manager.py`: CRUD operations

**Data Models**:
- `SessionRecord`: Chat session metadata
- `MessageRecord`: Individual messages
- `ToolCallRecord`: Tool execution logs

## Development Setup

### Prerequisites

- Python 3.10 or higher (3.12 recommended)
- Git
- Virtual environment tool (venv, conda, etc.)

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/arcon.git
cd arcon

# Create virtual environment with Python 3.12
python3.12 -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional)
pre-commit install
```

### Configuration

```bash
# Initialize .env
arcon config init

# Add API keys
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

## Code Organization

### Module Structure

```
src/arcon/
├── __init__.py          # Package initialization
├── core/                # Core abstractions
│   ├── types.py        # Type definitions, enums, dataclasses
│   ├── interface.py    # Abstract interfaces
│   └── session.py      # Session management
├── providers/           # LLM providers
│   ├── __init__.py
│   ├── anthropic.py
│   ├── openai.py
│   ├── ollama.py
│   └── resolver.py
├── tools/               # Tool system
│   ├── __init__.py
│   ├── base.py
│   ├── builtin.py
│   ├── registry.py
│   └── executor.py
├── agents/              # Agent system
│   ├── __init__.py
│   ├── base.py
│   ├── loader.py
│   └── registry.py
├── skills/              # Skills system
│   ├── __init__.py
│   ├── base.py
│   ├── loader.py
│   ├── registry.py
│   └── manager.py
├── storage/             # Persistence
│   ├── __init__.py
│   ├── models.py
│   └── manager.py
├── config/              # Configuration
│   ├── __init__.py
│   └── env.py
└── cli/                 # Command-line interface
    ├── __init__.py
    ├── main.py
    ├── chat.py
    ├── sessions.py
    └── config_cmd.py
```

### Naming Conventions

- **Files**: Snake case (`my_module.py`)
- **Classes**: Pascal case (`MyClass`)
- **Functions/Variables**: Snake case (`my_function`, `my_variable`)
- **Constants**: Upper snake case (`MY_CONSTANT`)
- **Private**: Leading underscore (`_private_method`)

### Import Style

```python
# Standard library imports
import os
from pathlib import Path
from typing import Optional, List

# Third-party imports
import yaml
from anthropic import AsyncAnthropic

# Local imports
from arcon.core.types import ProviderType, Message
from arcon.providers import ProviderResolver
```

## Testing Strategy

### Test Structure

```
tests/
├── test_core.py               # Core type system tests (22 tests)
├── test_providers.py          # Provider integration tests (20 tests)
├── test_tools.py              # Tool system tests (36 tests)
├── test_agents.py             # Agent system tests (32 tests)
├── test_skills.py             # Skills system tests (36 tests)
├── test_storage.py            # Storage layer tests (20 tests)
├── test_config.py             # Configuration tests (7 tests)
└── integration/               # Integration tests
    ├── test_end_to_end_chat.py
    ├── test_tool_workflows.py
    └── test_agent_routing.py
```

### Test Categories

#### Unit Tests

Focus: Individual components in isolation

```python
@pytest.mark.asyncio
async def test_anthropic_provider_creation():
    """Test Anthropic provider instantiation."""
    provider = AnthropicProvider(api_key="test-key")
    assert provider.config.model == "claude-3-5-sonnet-20241022"
```

#### Integration Tests

Focus: Component interactions

```python
@pytest.mark.asyncio
async def test_session_with_storage():
    """Test session persistence to database."""
    storage = StorageManager(":memory:")
    # ... test full workflow
```

#### End-to-End Tests

Focus: Complete user workflows

```python
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires API key"
)
@pytest.mark.asyncio
async def test_real_chat_flow():
    """Test actual chat with API."""
    # ... test with real API calls
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=arcon --cov-report=html

# Specific category
pytest tests/test_providers.py

# Integration only
pytest tests/integration/

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests in parallel
pytest -n auto
```

### Test Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
def temp_workspace():
    """Create temporary workspace."""
    workspace = Path(tempfile.mkdtemp())
    yield workspace
    shutil.rmtree(workspace, ignore_errors=True)

@pytest.fixture
def mock_provider():
    """Create mock LLM provider."""
    # ...
```

## Contributing Guidelines

### Workflow

1. **Fork** the repository
2. **Clone** your fork
3. **Create** a feature branch
4. **Develop** with tests
5. **Test** thoroughly
6. **Commit** with conventional commits
7. **Push** to your fork
8. **Open** a Pull Request

### Branch Naming

- Features: `feature/description`
- Bugs: `fix/description`
- Docs: `docs/description`
- Chores: `chore/description`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add skill relevance scoring
fix: correct agent routing priority
docs: update README with examples
chore: upgrade dependencies
test: add integration tests for tools
refactor: simplify provider resolver
```

### Code Style

#### Type Hints

Always use type hints:

```python
def process_message(
    message: str,
    max_length: int = 100
) -> tuple[str, int]:
    """Process message and return result."""
    # ...
```

#### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
    """
```

#### Error Handling

Be specific with exceptions:

```python
try:
    result = risky_operation()
except FileNotFoundError as e:
    raise ConfigError(f"Config file not found: {e}")
except ValueError as e:
    raise ValidationError(f"Invalid config value: {e}")
```

### Pull Request Process

1. **Update** documentation if needed
2. **Add** tests for new features
3. **Ensure** all tests pass
4. **Run** linting and type checking
5. **Update** CHANGELOG.md
6. **Request** review from maintainers

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Type hints complete
- [ ] Error handling appropriate
- [ ] Performance acceptable

## Release Process

### Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Steps

1. **Update** version in `pyproject.toml`
2. **Update** CHANGELOG.md
3. **Create** release branch: `release/v0.2.0`
4. **Test** thoroughly
5. **Merge** to main
6. **Tag** release: `git tag v0.2.0`
7. **Push** tags: `git push --tags`
8. **Build** distribution: `python -m build`
9. **Publish** to PyPI: `twine upload dist/*`
10. **Create** GitHub release with notes

---

**Questions?** Open an issue or discussion on GitHub!
