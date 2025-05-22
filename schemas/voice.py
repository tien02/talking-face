from pydantic import BaseModel

class IndianTextToSpeechInput(BaseModel):
    text:str
    speaker_id:str

class IndianTextToSpeechResponse(BaseModel):
    audio_base64: str = ""
    generate_time: float = 0
    duration: float = 0
    rtf: float = 0