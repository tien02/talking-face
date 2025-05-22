from pydantic import BaseModel

class SadTalkerAnimatorInput(BaseModel):
    driven_audio: str
    source_image: str

class SadTalkerAnimatorResponse(BaseModel):
    output_video: str
    total_time: float
    