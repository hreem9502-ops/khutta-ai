"""Application settings, loaded from environment variables or a local ``.env`` file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden through the environment."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", description="Google AI Studio API key.")
    gemini_api_key_backup: str = Field(
        default="", description="Backup keys (comma-separated), used when the main key's quota runs out."
    )
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: float = 25.0

    admin_token: str = Field(default="", description="Shared secret for the admin plan import; empty disables it.")

    cors_origins: list[str] = ["http://localhost:3000"]
    # Vercel rejects request bodies over 4.5 MB, so uploads are capped just below that.
    max_upload_bytes: int = 4 * 1024 * 1024
    plans_directory: Path = Path(__file__).resolve().parent / "data" / "plans"

    # Upstash Redis REST credentials (injected by the Vercel Marketplace integration).
    # When set, published plans are stored there instead of in ``plans_directory``.
    kv_rest_api_url: str = ""
    kv_rest_api_token: str = ""
    # How long a server instance trusts its in-memory copy of the plans before re-reading the store.
    plan_cache_seconds: float = 120.0

    @property
    def gemini_api_keys(self) -> list[str]:
        """Main key first, then backups, in the order they are tried."""
        raw = f"{self.gemini_api_key},{self.gemini_api_key_backup}"
        return [key.strip() for key in raw.split(",") if key.strip()]

    @property
    def ai_enabled(self) -> bool:
        """The AI advisor is only used when an API key is configured."""
        return bool(self.gemini_api_keys)

    @property
    def redis_enabled(self) -> bool:
        return bool(self.kv_rest_api_url.strip() and self.kv_rest_api_token.strip())


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
