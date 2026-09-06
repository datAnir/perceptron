# Arcon

**Arcon** is a robust AI coding assistant framework built on Everything Claude Code (ECC) foundations, featuring multi-provider LLM support, extensible agents, domain skills, and comprehensive tooling for software development workflows.

## ✨ Features

- **Multi-Provider LLM Support**: Seamlessly work with Anthropic Claude, OpenAI GPT, and local Ollama models
- **Extensible Agent System**: Specialized agents for coding, debugging, reviewing, testing, and documentation
- **Domain Skills**: 34+ pre-loaded skills from ECC covering API design, testing, frontend patterns, and more
- **Powerful Tool System**: Built-in file operations, bash execution, and extensible tool registry
- **Session Management**: Persistent conversation history with SQLite storage
- **Interactive CLI**: Full-featured command-line interface with streaming responses
- **Type-Safe**: Comprehensive type hints and validation throughout
- **Well-Tested**: 184+ passing tests with 95%+ coverage

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/arcon.git
cd arcon

# Create virtual environment (Python 3.10+ required)
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```bash
# Initialize configuration
arcon config init

# Edit .env and add your API keys
nano .env
```

Required environment variables:

```env
# Anthropic Claude API Key
ANTHROPIC_API_KEY=your-anthropic-key-here

# OpenAI API Key (optional)
OPENAI_API_KEY=your-openai-key-here

# Ollama base URL (for local models)
OLLAMA_BASE_URL=http://localhost:11434
```

### Basic Usage

#### Interactive Chat

```bash
# Start chat with default provider (Anthropic Claude)
arcon chat

# Use specific provider and model
arcon chat --provider anthropic --model claude-3-5-sonnet-20241022

# Use a specialized agent
arcon chat --agent Debugger

# Resume previous session
arcon chat --session 20240116-143052
```

#### Session Management

```bash
# List all chat sessions
arcon sessions list

# Show specific session details
arcon sessions show 20240116-143052

# Delete a session
arcon sessions delete 20240116-143052

# View database statistics
arcon sessions stats
```

#### Configuration Management

```bash
# Show current configuration
arcon config show

# Set configuration value
arcon config set DEFAULT_MODEL claude-3-5-sonnet-20241022

# Initialize .env template
arcon config init
```

#### Agents & Skills

```bash
# List available agents
arcon agents

# Filter agents by type
arcon agents --type debugging

# List available skills
arcon skills

# Filter skills by category
arcon skills --category development
```

## 📚 Architecture

### Core Components

```
arcon/
├── core/          # Core types, interfaces, session management
├── providers/     # LLM provider implementations (Anthropic, OpenAI, Ollama)
├── tools/         # Tool system (base, builtin, registry, executor)
├── agents/        # Agent system (base, loader, registry)
├── skills/        # Skills system (base, loader, registry, manager)
├── storage/       # SQLite persistence (models, manager)
├── config/        # Configuration management (.env loading)
└── cli/           # Command-line interface
```

### Key Concepts

**Providers**: Abstract LLM integrations supporting Claude, GPT, and Ollama models with streaming, tool use, and cost tracking.

**Agents**: Specialized AI personas with domain expertise, custom instructions, and tool permissions. Examples: CodingAssistant, Debugger, CodeReviewer, TestEngineer.

**Skills**: Reusable knowledge modules loaded from Markdown files, automatically injected into agent context based on relevance scoring.

**Tools**: Executable functions agents can invoke (file operations, bash commands). Extensible registry with built-in tools and custom tool support.

**Sessions**: Stateful conversations with message history, token tracking, cost calculation, and database persistence.

## 🎯 Use Cases

### Code Development

```bash
arcon chat --agent CodingAssistant
> Implement a binary search tree in Python with insert, search, and delete operations
```

### Debugging

```bash
arcon chat --agent Debugger
> Help me debug this error: AttributeError: 'NoneType' object has no attribute 'execute'
```

### Code Review

```bash
arcon chat --agent CodeReviewer
> Review this authentication module for security issues and best practices
```

### Test Generation

```bash
arcon chat --agent TestEngineer
> Write comprehensive unit tests for the UserRepository class
```

### Documentation

```bash
arcon chat --agent DocumentationWriter
> Create a README for my REST API project
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arcon --cov-report=html

# Run specific test file
pytest tests/test_providers.py

# Run integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Type checking
mypy src/arcon

# Linting
ruff check src/arcon

# Format code
ruff format src/arcon
```

### Project Structure

```
arcon/
├── src/arcon/         # Source code
├── tests/             # Unit and integration tests
├── agents/            # Agent YAML definitions
├── skills/            # Skill Markdown files (from ECC)
├── examples/          # Usage examples
├── pyproject.toml     # Project configuration
├── .env               # Environment variables (not in git)
└── README.md          # This file
```

## 📖 Advanced Features

### Custom Agents

Create custom agents using YAML:

```yaml
# agents/my-agent.yaml
name: "MyCustomAgent"
description: "Specialized agent for my domain"
type: "custom"
specialization: "my_domain"
tags:
  - "custom"
  - "specialized"

instructions: |
  You are an expert in my specific domain...
  
allowed_tools:
  - "read_file"
  - "write_file"
```

### Custom Skills

Create custom skills using Markdown with YAML frontmatter:

```markdown
---
name: my-skill
description: Domain knowledge for my use case
category: development
tags: ["custom", "domain"]
---

# My Custom Skill

Detailed knowledge and patterns for my domain...
```

### Programmatic Usage

```python
from arcon.providers import ProviderResolver
from arcon.core.types import ProviderType
from arcon.core.session import Session

# Initialize provider
provider = ProviderResolver.get_provider(ProviderType.ANTHROPIC)

# Create session
session = Session(provider=provider, working_dir="./workspace")

# Send message
async for chunk in session.send_message("Hello, world!"):
    if isinstance(chunk, dict) and chunk["type"] == "text":
        print(chunk["content"], end="", flush=True)
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure tests pass (`pytest`)
5. Commit with conventional commits (`git commit -m 'feat: add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built on foundations from **Everything Claude Code (ECC)**
- Inspired by multi-agent AI systems and coding assistants
- Leverages Claude, GPT, and open-source LLMs

## 📧 Contact

- **Project**: https://github.com/yourusername/arcon
- **Issues**: https://github.com/yourusername/arcon/issues
- **Discussions**: https://github.com/yourusername/arcon/discussions

---

**Made with ❤️ by the Arcon Team**
