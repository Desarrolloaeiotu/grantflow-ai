from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/grantflow"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # IA
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # Automatización
    N8N_BASE_URL: str = ""

    # Alertas
    RESEND_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""

    # Contactos (activar mes 5)
    APOLLO_API_KEY: str = ""

    # Grants premium (activar mes 6)
    INSTRUMENTL_API_KEY: str = ""

    # App
    NEXT_PUBLIC_API_URL: str = "http://localhost:3000"
    JWT_SECRET: str = "dev_secret_change_in_production"
    ENVIRONMENT: str = "development"

    # Tipo de cambio USD → COP (actualizar mensualmente)
    USD_TO_COP_RATE: float = 4050.0

    # Copilot Studio (S4.5)
    GRANTFLOW_API_KEY: str = ""
    COPILOT_TENANT_ID: str = ""
    COPILOT_CLIENT_ID: str = ""
    COPILOT_CLIENT_SECRET: str = ""

    @property
    def async_database_url(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
