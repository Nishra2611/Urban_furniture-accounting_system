from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://erp_user:erp_password@localhost:5432/erp_db"
    SECRET_KEY: str = "insecure-dev-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    class Config:
        env_file = ".env"


settings = Settings()
