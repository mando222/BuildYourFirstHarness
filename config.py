"""
Configuration: settings loaded from .env

We use load_dotenv(override=True) so the .env file always wins —
even if the shell has the variable set to an empty string.

@lru_cache turns get_settings() into a singleton: every module that
does "from config import settings" gets the same object.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load .env before anything reads os.environ.
# override=True means .env wins over empty shell variables.
load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    model: str
    max_tokens: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        model=os.getenv("MODEL", "claude-sonnet-4-5-20250929"),
        max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
    )


settings = get_settings()


if __name__ == "__main__":
    print(f"Model     : {settings.model}")
    print(f"Max tokens: {settings.max_tokens}")
    key = settings.anthropic_api_key
    key_preview = key[:8] + "..." if key else "(not set — add ANTHROPIC_API_KEY to .env)"
    print(f"API key   : {key_preview}")
