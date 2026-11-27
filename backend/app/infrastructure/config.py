from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    app_env: str = "local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def assert_usable(self) -> None:
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET debe tener al menos 32 caracteres.")
        if self.access_token_minutes < 1 or self.refresh_token_days < 1:
            raise RuntimeError("La vigencia de los tokens no es válida.")
        if not self.database_url.startswith("postgresql"):
            raise RuntimeError("DATABASE_URL debe ser PostgreSQL.")


def load_settings() -> Settings:
    settings = Settings()
    settings.assert_usable()
    return settings
