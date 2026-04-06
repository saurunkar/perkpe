from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Sentinel Finance OS Configuration.
    Settings are pulled from environment variables for production readiness.
    """
    # AlloyDB / Postgres Connection Settings
    ALLOYDB_HOST: str = "127.0.0.1"
    ALLOYDB_PORT: int = 5432
    ALLOYDB_USER: str = "postgres"
    ALLOYDB_DB: str = "sentinel_db"
    ALLOYDB_PASSWORD: Optional[str] = None
    
    # Vertex AI / GCP Settings
    GCP_PROJECT_ID: str = "gdgpune-455206"
    GCP_REGION: str = "us-central1"
    
    # Application Settings
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global configuration instance
settings = Settings()

def get_db_url() -> str:
    """Constructs the connection string for AlloyDB."""
    if settings.ALLOYDB_PASSWORD:
        return f"postgresql://{settings.ALLOYDB_USER}:{settings.ALLOYDB_PASSWORD}@{settings.ALLOYDB_HOST}:{settings.ALLOYDB_PORT}/{settings.ALLOYDB_DB}"
    return f"postgresql://{settings.ALLOYDB_USER}@{settings.ALLOYDB_HOST}:{settings.ALLOYDB_PORT}/{settings.ALLOYDB_DB}"
