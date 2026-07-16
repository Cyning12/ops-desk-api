"""Application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "ops-desk-api"
    debug: bool = False

    # Database
    database_url: str = Field(default="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk")
    database_echo: bool = False

    # Auth
    ops_desk_secret: str = Field(default="change-me")
    ops_desk_auth_mode: str = Field(default="db")  # db | hmac
    session_cookie_name: str = "ops_session"
    session_ttl_hours: int = 168  # 7 days

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # LLM
    ops_llm_provider: str = Field(default="siliconflow")
    ops_llm_model: str = Field(default="Qwen/Qwen2.5-72B-Instruct")

    siliconflow_base_url: str = Field(default="https://api.siliconflow.cn/v1")
    siliconflow_api_key: str | None = None
    bailian_api_key: str | None = None
    bailian_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    bailian_model: str = Field(default="qwen-plus")

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
