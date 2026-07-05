from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Social Platform Transparency Dashboard"
    database_url: str = "sqlite:///./database/social_platform_transparency.db"
    frontend_origin: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    data_dir: Path = Path("database")
    cache_dir: Path = Path("database/cache")
    user_agent: str = "SocialPlatformTransparencyDashboard/1.0 (+official-data-only)"
    request_timeout_seconds: int = 30
    scheduler_interval_minutes: int = 720

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.cache_dir.mkdir(parents=True, exist_ok=True)
