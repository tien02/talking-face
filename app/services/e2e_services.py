# import base64

# from ray import serve
# from ray.serve.handle import DeploymentHandle

# @serve.deployment(ray_actor_options={"num_cpus": 0.5})
# class VideoGenerator:
#     def __init__(self, tts_handle:DeploymentHandle, sadtalker_handle:DeploymentHandle):
#         self.tts = tts_handle
#         self.sadtalker = sadtalker_handle

#     async def __call__(self, text: str, speaker_id: str, image_bytes: bytes):

#         # Step 1: Text → Speech
#         audio_base64: str = await self.tts.remote(text, speaker_id)
#         audio_bytes = base64.b64decode(audio_base64)

#         # Step 2: Speech + Image → Video
#         video_base64: str = await self.sadtalker.remote(audio_bytes, image_bytes)

#         return {"video_base64": video_base64}

from ray import serve
from ray.serve.handle import DeploymentHandle
from fastapi import FastAPI
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

        video_path = video_response.output_video

        with open(video_path, "rb") as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        return {"video_base64": video_base64, "total_time": video_response.total_time}
