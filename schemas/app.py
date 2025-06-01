from pydantic import BaseModel

class GenerationRequest(BaseModel):
    text: str
    speaker_id: str
    image_bytes: str

class StreamRequest(BaseModel):
    sdp: str
    type: str
    session_id: str