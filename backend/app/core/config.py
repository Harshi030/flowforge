from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    env: str = "local"
    log_level: str = "INFO"
    database_url: str  # no default — think about why
    redis_url: str  # no default — same question
