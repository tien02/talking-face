from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    MINIO_HOST: str
    MINIO_USER_NAME: str
    MINIO_USER_PWD: str

data_settings = DataSettings()