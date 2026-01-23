from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "jobrunner-api"
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/jobrunner"

settings = Settings()