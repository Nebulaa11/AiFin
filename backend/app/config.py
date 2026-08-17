from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./aifin.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    google_client_id: str = ""
    jwt_secret: str = "aifin-dev-secret-change-in-production"
    jwt_expire_hours: int = 168
    allow_dev_auth: bool = False

    @property
    def dev_auth_enabled(self) -> bool:
        return not self.google_client_id or self.allow_dev_auth


@lru_cache
def get_settings() -> Settings:
    return Settings()
