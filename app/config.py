from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Database ----
    database_url: str = Field(..., description="PostgreSQL connection URL (Neon)")

    # ---- LLM providers ----
    # Raw comma-separated strings; split lazily via properties below.
    groq_keys_raw: str = Field("", alias="GROQ_KEYS")
    openrouter_keys_raw: str = Field("", alias="OPENROUTER_KEYS")

    # Single-key fallback used by some agents that don't go through the pool.
    groq_api_key: str = Field("", alias="GROQ_API_KEY")

    # ---- Search ----
    tavily_api_key: str = Field("", alias="TAVILY_API_KEY")

    # ---- HTTP ----
    cors_origins_raw: str = Field("*", alias="CORS_ORIGINS")


    whatsapp_number: str = Field("", alias="WHATSAPP_NUMBER")

    admin_username: str = Field(..., alias="ADMIN_USERNAME")
    admin_password_hash: str = Field(..., alias="ADMIN_PASSWORD_HASH")

    #run this command to generate new one : python -c "import secrets; print(secrets.token_urlsafe(64))"
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")

    jwt_expire_minutes: int = Field(480, alias="JWT_EXPIRE_MINUTES")
    
    # ---- Derived ----
    @property
    def groq_keys(self) -> list[str]:
        return [k.strip() for k in self.groq_keys_raw.split(",") if k.strip()]

    @property
    def openrouter_keys(self) -> list[str]:
        return [k.strip() for k in self.openrouter_keys_raw.split(",") if k.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


settings = Settings()