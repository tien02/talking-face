from pydantic import BaseModel
from typing import Optional, Literal


class GenerationRequest(BaseModel):
    text: str
    speaker_id: str
    image_bytes: str

class GetGenerationStatus(BaseModel):
    status: Literal['STARTED', 'SUCCESS', 'FAIL']
    message: Optional[str] = None
