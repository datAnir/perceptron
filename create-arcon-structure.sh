#!/bin/bash

# Create Arcon folder structure for ECC-based coding agent
# Location: /home/anirband/perceptron/arcon/

set -e

ARCON_ROOT="/home/anirband/perceptron/arcon"

echo "📁 Creating Arcon folder structure at $ARCON_ROOT..."

# Create main directories
mkdir -p "$ARCON_ROOT/src/arcon/core"
mkdir -p "$ARCON_ROOT/src/arcon/providers"
mkdir -p "$ARCON_ROOT/src/arcon/tools"
mkdir -p "$ARCON_ROOT/src/arcon/agents"
mkdir -p "$ARCON_ROOT/src/arcon/skills"
mkdir -p "$ARCON_ROOT/src/arcon/storage"
mkdir -p "$ARCON_ROOT/src/arcon/cli"
mkdir -p "$ARCON_ROOT/src/arcon/config"

# Create agents and skills directories
mkdir -p "$ARCON_ROOT/agents"
mkdir -p "$ARCON_ROOT/skills"

# Create tests directory
mkdir -p "$ARCON_ROOT/tests"

# Create examples directory
mkdir -p "$ARCON_ROOT/examples"

# Create initial Python package files
touch "$ARCON_ROOT/src/arcon/__init__.py"
touch "$ARCON_ROOT/src/arcon/__main__.py"
touch "$ARCON_ROOT/src/arcon/core/__init__.py"
touch "$ARCON_ROOT/src/arcon/core/interface.py"
touch "$ARCON_ROOT/src/arcon/core/types.py"
touch "$ARCON_ROOT/src/arcon/core/session.py"

touch "$ARCON_ROOT/src/arcon/providers/__init__.py"
touch "$ARCON_ROOT/src/arcon/providers/base.py"
touch "$ARCON_ROOT/src/arcon/providers/anthropic.py"
touch "$ARCON_ROOT/src/arcon/providers/openai.py"
touch "$ARCON_ROOT/src/arcon/providers/ollama.py"
touch "$ARCON_ROOT/src/arcon/providers/resolver.py"

touch "$ARCON_ROOT/src/arcon/tools/__init__.py"
touch "$ARCON_ROOT/src/arcon/tools/base.py"
touch "$ARCON_ROOT/src/arcon/tools/registry.py"
touch "$ARCON_ROOT/src/arcon/tools/executor.py"

touch "$ARCON_ROOT/src/arcon/agents/__init__.py"
touch "$ARCON_ROOT/src/arcon/agents/base.py"
touch "$ARCON_ROOT/src/arcon/agents/registry.py"
touch "$ARCON_ROOT/src/arcon/agents/loader.py"

touch "$ARCON_ROOT/src/arcon/skills/__init__.py"
touch "$ARCON_ROOT/src/arcon/skills/base.py"
touch "$ARCON_ROOT/src/arcon/skills/registry.py"
touch "$ARCON_ROOT/src/arcon/skills/loader.py"
touch "$ARCON_ROOT/src/arcon/skills/manager.py"

touch "$ARCON_ROOT/src/arcon/storage/__init__.py"
touch "$ARCON_ROOT/src/arcon/storage/base.py"
touch "$ARCON_ROOT/src/arcon/storage/sqlite.py"

touch "$ARCON_ROOT/src/arcon/cli/__init__.py"
touch "$ARCON_ROOT/src/arcon/cli/selector.py"
touch "$ARCON_ROOT/src/arcon/cli/commands.py"

touch "$ARCON_ROOT/src/arcon/config/__init__.py"
touch "$ARCON_ROOT/src/arcon/config/manager.py"

# Create test files
touch "$ARCON_ROOT/tests/__init__.py"
touch "$ARCON_ROOT/tests/test_providers.py"
touch "$ARCON_ROOT/tests/test_tools.py"
touch "$ARCON_ROOT/tests/test_agents.py"
touch "$ARCON_ROOT/tests/test_skills.py"
touch "$ARCON_ROOT/tests/test_storage.py"
touch "$ARCON_ROOT/tests/integration_test.py"

# Create example files
touch "$ARCON_ROOT/examples/basic_invoke.py"
touch "$ARCON_ROOT/examples/with_tools.py"
touch "$ARCON_ROOT/examples/session_persistence.py"

# Create configuration files
touch "$ARCON_ROOT/pyproject.toml"
touch "$ARCON_ROOT/.env.example"
touch "$ARCON_ROOT/README.md"
touch "$ARCON_ROOT/DEVELOPMENT.md"

echo "✅ Arcon folder structure created successfully!"
echo ""
echo "📋 Structure:"
tree -L 3 "$ARCON_ROOT" 2>/dev/null || find "$ARCON_ROOT" -type d | sort | sed 's|[^/]*/|  |g'

echo ""
echo "📖 Next steps:"
echo "  1. cd $ARCON_ROOT"
echo "  2. Configure pyproject.toml with dependencies"
echo "  3. Create .env with your API keys"
echo "  4. Begin implementing Step 2 (core types and interfaces)"
