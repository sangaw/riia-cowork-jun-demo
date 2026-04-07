"""
RITA production configuration.

Loads base.yaml then deep-merges the environment-specific YAML on top.
Secrets are sourced exclusively from environment variables — never from YAML.

Environment selection:
    RITA_ENV=development  (default)
    RITA_ENV=staging
    RITA_ENV=production

Required env vars in staging/production:
    RITA_JWT_SECRET   — min 32-char secret for JWT signing
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Config directory resolution
# ---------------------------------------------------------------------------
# __file__ = riia-jun-release/src/rita/config.py
# .parent = rita/  .parent = src/  .parent = riia-jun-release/
_CONFIG_DIR: Path = Path(__file__).parent.parent.parent / "config"


# ---------------------------------------------------------------------------
# Deep-merge helper
# ---------------------------------------------------------------------------

def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Nested settings models
# ---------------------------------------------------------------------------

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    name: str = "rita"
    version: str = "1.0.0"


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"


class DataSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    input_dir: str = "rita_input"
    output_dir: str = "rita_output"


class ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    path: str = "rita_output/models"


class InstrumentConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    lot_size: int


class InstrumentsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    nifty: InstrumentConfig = InstrumentConfig(lot_size=75)
    banknifty: InstrumentConfig = InstrumentConfig(lot_size=30)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    database_url: str = "sqlite:///./rita_output/rita.db"


class SecuritySettings(BaseSettings):
    """
    Security settings.

    jwt_secret is sourced exclusively from the RITA_JWT_SECRET environment
    variable and is never loaded from YAML.  In staging/production, the
    absence of this variable raises a ValueError at startup.
    """

    model_config = SettingsConfigDict(extra="forbid", env_prefix="RITA_")

    jwt_secret: SecretStr = Field(
        default=SecretStr("dev-secret-change-in-prod"),
        validation_alias="RITA_JWT_SECRET",
    )
    cors_origins: list[str] = ["http://localhost:8000"]


# ---------------------------------------------------------------------------
# Root Settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Root application settings.

    Constructed by loading base.yaml and deep-merging the environment-specific
    YAML on top.  Secrets are injected from environment variables only.
    """

    model_config = SettingsConfigDict(extra="forbid")

    app: AppSettings = AppSettings()
    server: ServerSettings = ServerSettings()
    data: DataSettings = DataSettings()
    model: ModelSettings = ModelSettings()
    instruments: InstrumentsSettings = InstrumentsSettings()
    security: SecuritySettings = SecuritySettings()
    database: DatabaseSettings = DatabaseSettings()

    # The active environment name (informational — used during construction).
    env: str = "development"

    @classmethod
    def _load_yaml_config(cls) -> dict[str, Any]:
        """Load and merge base + environment-specific YAML config."""
        rita_env = os.environ.get("RITA_ENV", "development").lower()

        base_path = _CONFIG_DIR / "base.yaml"
        env_path = _CONFIG_DIR / f"{rita_env}.yaml"

        with base_path.open() as fh:
            merged: dict[str, Any] = yaml.safe_load(fh) or {}

        if env_path.exists():
            with env_path.open() as fh:
                env_cfg: dict[str, Any] = yaml.safe_load(fh) or {}
            merged = _deep_merge(merged, env_cfg)

        # Strip jwt_secret from YAML if it accidentally appears — secrets come
        # from env vars only.
        merged.get("security", {}).pop("jwt_secret", None)

        merged["env"] = rita_env
        return merged

    @model_validator(mode="before")
    @classmethod
    def _build_from_yaml(cls, values: Any) -> Any:
        """Pre-populate field values from YAML before env-var overrides apply."""
        if not isinstance(values, dict):
            return values

        yaml_cfg = cls._load_yaml_config()

        # Merge YAML into any explicitly passed values (passed values win).
        merged = _deep_merge(yaml_cfg, values)
        return merged

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        """Enforce that RITA_JWT_SECRET is set in non-development environments."""
        if self.env in ("staging", "production"):
            secret_val = self.security.jwt_secret.get_secret_value()
            if not secret_val or secret_val == "dev-secret-change-in-prod":
                raise ValueError(
                    f"RITA_JWT_SECRET environment variable must be set to a strong "
                    f"secret in the '{self.env}' environment."
                )
            if len(secret_val) < 32:
                raise ValueError(
                    "RITA_JWT_SECRET must be at least 32 characters long."
                )
        return self


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

settings: Settings = Settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton (use with FastAPI Depends)."""
    return settings
