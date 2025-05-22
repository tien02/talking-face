from pydantic_settings import BaseSettings, SettingsConfigDict


class VideoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    VIDEO_BATCH_SIZE: int
    VIDEO_DEVICE: str
    USE_VIDEO_TRT_MODEL: bool

video_settings = VideoSettings()