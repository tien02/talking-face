from pydantic import BaseModel
from typing import Optional, Literal


class GenerationRequest(BaseModel):
    text: str
    speaker_id: Literal['male', 'female', 'random']
    alpha: float | None = None
    threshold: float | None = None

class GetGenerationStatus(BaseModel):
    status: Literal['STARTED', 'SUCCESS', 'FAIL']
    message: Optional[str] = None
