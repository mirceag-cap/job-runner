from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://app:app@localhost:55432/jobrunner"
    poll_interval_seconds: float = 1.0
    retry_base_delay_seconds: int = 2
    retry_max_delay_seconds: int = 60

settings = Settings()