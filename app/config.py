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

    # Checkout / Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    checkout_currency: str = "usd"
    checkout_digital_price_cents: int = 1695
    checkout_print_price_cents: int = 1995
    checkout_success_url: str = "http://localhost:3000/checkout/success"
    checkout_cancel_url: str = "http://localhost:3000/checkout/cancel"
    checkout_expert_check_price_cents: int = 799
    checkout_retouching_price_cents: int = 499
    checkout_demo_mode: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key.strip())


settings = Settings()
