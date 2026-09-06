"""Environment variable configuration management."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from ..core.types import ProviderConfig, ProviderType


# Track if environment has been loaded
_ENV_LOADED = False


def load_config(env_file: Optional[Path] = None) -> None:
    """Load configuration from .env file.
    
    Args:
        env_file: Path to .env file (default: searches parent directories)
    """
    global _ENV_LOADED
    
    if _ENV_LOADED:
        return
    
    if env_file:
        load_dotenv(env_file)
    else:
        # Search for .env file in current and parent directories
        load_dotenv(dotenv_path=find_env_file())
    
    _ENV_LOADED = True


def find_env_file() -> Optional[Path]:
    """Find .env file in current or parent directories.
    
    Returns:
        Path to .env file or None if not found
    """
    current = Path.cwd()
    
    # Check current directory and parents
    for parent in [current] + list(current.parents):
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    
    return None


def get_api_key(provider_type: ProviderType, api_key: Optional[str] = None) -> Optional[str]:
    """Get API key with fallback to environment variables.
    
    Args:
        provider_type: Type of provider
        api_key: Explicit API key (takes precedence)
        
    Returns:
        API key or None if not found
    """
    # Ensure env is loaded
    load_config()
    
    # Explicit key takes precedence
    if api_key:
        return api_key
    
    # Map provider types to env var names
    env_var_map = {
        ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
        ProviderType.OPENAI: "OPENAI_API_KEY",
    }
    
    env_var = env_var_map.get(provider_type)
    if env_var:
        return os.getenv(env_var)
    
    return None


def get_provider_config(
    provider_type: ProviderType,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> ProviderConfig:
    """Create provider config with env var fallback.
    
    Args:
        provider_type: Type of provider
        api_key: API key (falls back to env var)
        model: Model name (falls back to env var)
        **kwargs: Additional config options
        
    Returns:
        Provider configuration
    """
    # Ensure env is loaded
    load_config()
    
    # Get API key with fallback
    resolved_api_key = get_api_key(provider_type, api_key)
    
    # Get model with fallback to env var
    if not model:
        model = os.getenv("DEFAULT_MODEL")
    
    # Get other optional settings from env
    if "temperature" not in kwargs:
        temp = os.getenv("DEFAULT_TEMPERATURE")
        if temp:
            kwargs["temperature"] = float(temp)
    
    if "max_tokens" not in kwargs:
        max_tok = os.getenv("MAX_TOKENS")
        if max_tok:
            kwargs["max_tokens"] = int(max_tok)
    
    # Ollama-specific: base_url from env
    if provider_type == ProviderType.OLLAMA:
        if "base_url" not in kwargs:
            base_url = os.getenv("OLLAMA_BASE_URL")
            if base_url:
                kwargs["base_url"] = base_url
    
    return ProviderConfig(
        provider_type=provider_type,
        api_key=resolved_api_key,
        model=model,
        **kwargs
    )


def get_database_path() -> Path:
    """Get database path from environment or default.
    
    Returns:
        Path to SQLite database
    """
    load_config()
    db_path = os.getenv("DATABASE_PATH", "arcon.db")
    return Path(db_path)


def get_log_level() -> str:
    """Get log level from environment or default.
    
    Returns:
        Log level (INFO, DEBUG, WARNING, ERROR)
    """
    load_config()
    return os.getenv("LOG_LEVEL", "INFO")


def get_log_file() -> Optional[Path]:
    """Get log file path from environment.
    
    Returns:
        Path to log file or None
    """
    load_config()
    log_file = os.getenv("LOG_FILE")
    return Path(log_file) if log_file else None
