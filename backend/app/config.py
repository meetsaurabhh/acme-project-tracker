"""Application settings, read from environment variables or a .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Where the database lives. Docker Compose overrides this.
    database_url: str = "postgresql+psycopg2://acme:acme@localhost:5432/acme_pm"

    # Used to sign login tokens. CHANGE THIS in a real deployment.
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480  # 8 hours

    # Which frontend origins are allowed to call this API.
    cors_origins: str = "http://localhost:3030,http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
