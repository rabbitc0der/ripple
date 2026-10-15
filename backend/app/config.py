from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_PASSWORD: Optional[str] = None

    APP_ENV: str = "development"
    PORT: int = 8000
    FRONTEND_PORT: int = 5173

    # LLM Execution Mode: "deterministic" | "cached" | "live"
    LLM_MODE: str = "deterministic"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Graph Names
    DEFAULT_GRAPH: str = "tenant_a"
    TEMPLATE_GRAPH: str = "template_golden"

settings = Settings()
