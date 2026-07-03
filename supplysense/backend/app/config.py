"""
Centralized application configuration.

All runtime configuration is sourced from environment variables (and a local
.env file in development). Nothing here should ever hold real secrets —
defaults are intentionally non-functional placeholders that force an explicit
.env to be supplied.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- Application ----
    app_name: str = "AI Supply Chain Copilot"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ---- Security ----
    secret_key: str = "insecure-dev-key-change-me"
    access_token_expire_minutes: int = 60

    # ---- MongoDB Atlas ----
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "supply_chain_copilot"
    mongodb_vector_index: str = "vector_index"
    mongodb_vector_dimensions: int = 1024

    # ---- Amazon Bedrock ----
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_max_tokens: int = 2048
    bedrock_temperature: float = 0.2

    # ---- Voyage AI ----
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"
    voyage_input_type_document: str = "document"
    voyage_input_type_query: str = "query"

    # ---- Agents ----
    agent_max_iterations: int = 8
    agent_recursion_limit: int = 25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so we parse the environment exactly once."""
    return Settings()
