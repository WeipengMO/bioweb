from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIOWEB_", env_file=".env", extra="ignore")

    app_name: str = "BioWeb"
    database_url: str = "postgresql+psycopg://bioweb:bioweb@localhost:5432/bioweb"
    redis_url: str = "redis://localhost:6379/0"
    data_dir: Path = Path("data")
    results_dir: Path = Path("data/results")
    sync_analysis: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


settings = Settings()

