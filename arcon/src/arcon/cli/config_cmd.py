"""Configuration management commands."""
import os
from pathlib import Path

from ..config import load_config, find_env_file


class ConfigManager:
    """Manage configuration."""
    
    def __init__(self):
        """Initialize config manager."""
        load_config()
    
    def show_config(self):
        """Show current configuration."""
        env_file = find_env_file()
        
        print("\n⚙️  Current Configuration:")
        print("=" * 80)
        
        if env_file:
            print(f"Config file: {env_file}")
        else:
            print("Config file: Not found (using defaults)")
        
        print("\nAPI Keys:")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        print(f"  ANTHROPIC_API_KEY: {'✓ Set' if anthropic_key else '✗ Not set'}")
        print(f"  OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set'}")
        
        print("\nProvider Settings:")
        print(f"  DEFAULT_PROVIDER: {os.getenv('DEFAULT_PROVIDER', 'anthropic')}")
        print(f"  DEFAULT_MODEL: {os.getenv('DEFAULT_MODEL', 'claude-3-5-sonnet-20241022')}")
        print(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
        
        print("\nGeneral Settings:")
        print(f"  MAX_TOKENS: {os.getenv('MAX_TOKENS', '4096')}")
        print(f"  DEFAULT_TEMPERATURE: {os.getenv('DEFAULT_TEMPERATURE', '0.7')}")
        print(f"  DATABASE_PATH: {os.getenv('DATABASE_PATH', 'arcon.db')}")
        print(f"  LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
        print()
    
    def set_config(self, key: str, value: str):
        """Set configuration value."""
        env_file = find_env_file()
        
        if not env_file:
            print("\n❌ No .env file found. Run 'arcon config init' to create one.")
            return
        
        # Read current content
        content = env_file.read_text()
        lines = content.split('\n')
        
        # Update or append
        key_upper = key.upper()
        found = False
        
        for i, line in enumerate(lines):
            if line.startswith(f"{key_upper}="):
                lines[i] = f"{key_upper}={value}"
                found = True
                break
        
        if not found:
            lines.append(f"{key_upper}={value}")
        
        # Write back
        env_file.write_text('\n'.join(lines))
        
        print(f"\n✅ Configuration updated: {key_upper}={value}")
        print(f"   File: {env_file}")
        print()
    
    def init_env(self):
        """Initialize .env file."""
        env_file = Path.cwd() / ".env"
        
        if env_file.exists():
            response = input(f"\n⚠️  .env file already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        # Template content
        template = """# LLM Provider API Keys
# ======================

# Anthropic Claude API Key
# Get yours at: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OpenAI API Key
# Get yours at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key-here

# Ollama Configuration (for local models)
# Default: http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Storage Configuration
# ======================

# SQLite database path (relative to project root)
DATABASE_PATH=arcon.db

# Session Configuration
# ======================

# Default model configuration
DEFAULT_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-sonnet-20241022

# Token limits
MAX_TOKENS=4096
DEFAULT_TEMPERATURE=0.7

# Logging
# ======================

LOG_LEVEL=INFO
LOG_FILE=arcon.log
"""
        
        env_file.write_text(template)
        
        print(f"\n✅ Created .env file: {env_file}")
        print("\n📝 Next steps:")
        print("   1. Edit .env and add your API keys")
        print("   2. Add .env to .gitignore (if not already)")
        print()
