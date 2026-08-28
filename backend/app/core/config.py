from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    env: str = "local"
    log_level: str = "INFO"
    database_url: str 
    redis_url: str  
    jwt_secret:str
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 900  # 15 mins 
