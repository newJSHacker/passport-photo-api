from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Passport Photo API"
    debug: bool = True
    cors_origins: str = "http://localhost:3000"
    storage_path: str = "storage"
    max_upload_mb: int = 10
    background_remover: str = "modnet"
    watermark_enabled: bool = True
    watermark_text: str = "Passport-Photo.online"
    database_url: str = (
        "postgresql+asyncpg://passport:passport@127.0.0.1:5432/passport_photo"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
