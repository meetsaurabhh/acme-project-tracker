"""Application settings. Single source of truth for every environment value."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Values are read from environment variables, falling back to .env."""

    # --- Application identity ---
    app_name: str = "ACME Project Tracker API"
    app_version: str = "2.0.0"
    api_v1_prefix: str = "/api"

    # --- Database ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/acme_pm"

    # --- Authentication ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480

    # --- Cross-origin access (comma separated list of allowed front ends) ---
    cors_origins: str = "http://localhost:3030"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> list[str]:
        """Split the comma separated string into the list FastAPI expects."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
