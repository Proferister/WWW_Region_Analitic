from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MAX Bot
    MAX_BOT_TOKEN: str
    WEBHOOK_URL: str

    # Telegram Bot
    TG_BOT_TOKEN: str
    TG_WEBHOOK_URL: str

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL
    DATABASE_URL: str

    # Mail API
    MAIL_API_URL: str = "https://whitea.ru/api/mail/send"
    MAIL_API_KEY: str

    # GigaChat (AI Analyze)
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_VERIFY_SSL: str = "false"

    # Auth
    OTP_LENGTH: int = 6
    OTP_EXPIRE_SECONDS: int = 300  # 5 минут
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 1440  # 24 часа

    model_config = {"env_file": ".env"}


settings = Settings()
