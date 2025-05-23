from ray import serve
from ray.serve.handle import DeploymentHandle
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import base64

app = FastAPI()

class GenerationRequest(BaseModel):
    text: str
    speaker_id: str
    image_bytes: str  # base64 encoded image

@serve.deployment(ray_actor_options={"num_cpus": 0.5})
@serve.ingress(app)
class VideoGenerator:
    def __init__(self, tts_handle: DeploymentHandle, sadtalker_handle: DeploymentHandle):
        self.tts = tts_handle
        self.sadtalker = sadtalker_handle

    @app.post("/generate")
    async def generate(self, request: GenerationRequest):
        text = request.text
        speaker_id = request.speaker_id
        image_bytes = base64.b64decode(request.image_bytes)

        # Call TTS service
        audio_base64: str = await self.tts.remote(text, speaker_id)
        audio_bytes = base64.b64decode(audio_base64)

        # Call SadTalker
        video_response: dict = await self.sadtalker.remote(audio_bytes, image_bytes)
        video_path:str = video_response.output_video

        # Open file and stream
        def iterfile():
            with open(video_path, mode="rb") as file_like:
                yield from file_like

        return StreamingResponse(iterfile(), media_type="video/mp4")
