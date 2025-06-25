import json
import base64
from redis.asyncio import Redis

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from ray import serve
from ray.serve.handle import DeploymentHandle

from config.data import data_settings
from schemas.app import GenerationRequest, GetGenerationStatus

app = FastAPI()
redis_client = Redis(
    host=data_settings.REDIS_HOST,
    port=data_settings.REDIS_PORT,
    db=data_settings.REDIS_DB
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@serve.deployment(ray_actor_options={"num_cpus": 4})
@serve.ingress(app)
class VideoGenerator:
    def __init__(self, tts_handle: DeploymentHandle, sadtalker_handle: DeploymentHandle):
        self.tts = tts_handle
        self.sadtalker = sadtalker_handle

    @app.post("/generate")
    async def generate(self, inp: GenerationRequest):
        text = inp.text
        speaker_id = inp.speaker_id
        image_bytes = base64.b64decode(inp.image_bytes)

        # Call TTS service
        audio_base64: str = await self.tts.remote(text, speaker_id)
        audio_bytes = base64.b64decode(audio_base64)

        # Call SadTalker
        video_gen_resp: dict = await self.sadtalker.remote(audio_bytes, image_bytes)

        return video_gen_resp

    @app.get("/video")
    async def stream(self, session_id) -> GetGenerationStatus:
        session_data = await redis_client.get(session_id)

        if session_data is None:
            raise HTTPException(status_code=404, detail="Session not found")

        session = json.loads(session_data)

        return GetGenerationStatus(
            status=session["status"],
            message=session["remote_path"]
            )
