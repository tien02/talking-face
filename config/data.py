from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    MINIO_HOST: str
    MINIO_USER_NAME: str
    MINIO_USER_PWD: str
    MINIO_BUCKET: str

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

data_settings = DataSettings()