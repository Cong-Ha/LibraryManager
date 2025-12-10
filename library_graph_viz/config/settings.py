"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # MySQL Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "library"
    mysql_olap_database: str = "library_olap"
    mysql_user: str = "root"
    mysql_password: str = "librarypass123"

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "librarypass123"

    # Application Settings
    debug: bool = False
    log_level: str = "INFO"

    # Export Settings
    export_dir: str = "./exports"

    @property
    def mysql_connection_string(self) -> dict:
        """Return MySQL connection parameters as a dictionary."""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "database": self.mysql_database,
            "user": self.mysql_user,
            "password": self.mysql_password,
        }

    @property
    def export_path(self) -> Path:
        """Return the export directory as a Path object."""
        path = Path(self.export_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once.
    Clear cache with get_settings.cache_clear() if needed.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
