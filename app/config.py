"""Application configuration."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# pydantic Settings 只把认识的字段读进对象；reranker / tracing 用 os.getenv。
# 按本文件定位仓根 .env，不依赖 uvicorn 的 cwd。
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


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
    session_cookie_path: str = "/"
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"

    # Admin sync 机读 Bearer；空字符串则禁用 Bearer 路径（仅 cookie maintainer）
    ops_admin_sync_token: str = Field(default="")

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Chat WebSocket transport (unauthenticated demo; must be false in production)
    ops_chat_ws_enabled: bool = True

    # Capability · 真 MCP client（U3；默认关，禁止 CI 外网）
    ops_capability_mcp_enabled: bool = False
    ops_capability_mcp_endpoint: str | None = None
    ops_capability_mcp_default_tool: str | None = None

    # LLM
    ops_llm_provider: str = Field(default="siliconflow")
    ops_llm_model: str | None = Field(default=None)

    siliconflow_base_url: str = Field(default="https://api.siliconflow.cn/v1")
    siliconflow_api_key: str | None = None
    bailian_api_key: str | None = None
    bailian_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    bailian_model: str = Field(default="qwen-plus")

    @model_validator(mode="after")
    def _set_default_llm_model(self) -> "Settings":
        """Use model_catalog default when ops_llm_model is unset or empty.

        Empty string matters: compose/env injection of `OPS_LLM_MODEL=`
        would otherwise leak through as `model: ""` in chat done events.
        """
        if not self.ops_llm_model:
            from app.llm.model_catalog import get_default_model

            self.ops_llm_model = get_default_model(self.ops_llm_provider)
        return self

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
