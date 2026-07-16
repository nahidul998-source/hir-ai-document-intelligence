from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class ApplicationSettings(BaseSettings):
    app_name: str = "HIR Platform API"
    environment: str = "development"
    debug: bool = True
    api_v1_str: str = "/api/v1"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

class DatabaseSettings(BaseSettings):
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hir_db"
    pool_size: int = 5
    max_overflow: int = 10

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")

class SecuritySettings(BaseSettings):
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_prefix="SECURITY_", env_file=".env", extra="ignore")

class QueueSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    
    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_", env_file=".env", extra="ignore")

class AISettings(BaseSettings):
    provider_config_path: str = "configs/ai.yaml"

    model_config = SettingsConfigDict(env_prefix="AI_", env_file=".env", extra="ignore")

class Settings(BaseSettings):
    app: ApplicationSettings = ApplicationSettings()
    db: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    queue: QueueSettings = QueueSettings()
    ai: AISettings = AISettings()

settings = Settings()
