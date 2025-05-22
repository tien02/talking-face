from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    VOICE_ATTN_IMPLEMENTATION: str
    VOICE_DEVICE: str
    VOICE_MODEL_NAME_OR_PATH: str


audio_settings = VoiceSettings()