import json
import uuid
import base64
import logging
from redis.asyncio import Redis

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ray import serve
from ray.serve.handle import DeploymentHandle

from common.face import INTERVIEWER_AVATAR
from config.data import data_settings
from schemas.app import GenerationRequest, GetGenerationStatus
from src.data.vectordb import WeviateClient

app = FastAPI()

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

        self.redis_client = Redis(
            host=data_settings.REDIS_HOST,
            port=data_settings.REDIS_PORT,
            db=data_settings.REDIS_DB
        )

        self.logger = logging.getLogger("ray")

    @app.post("/generate")
    async def generate(self, inp: GenerationRequest):
        text = inp.text
        speaker_id = inp.speaker_id

        weviate_client = WeviateClient(
            host=data_settings.VECTOR_SEARCH_HOST,
            port=data_settings.VECTOR_SEARCH_PORT
            )

        search_alpha = inp.alpha if inp.alpha is not None else data_settings.VECTOR_SEARCH_ALPHA
        search_threshold = inp.threshold if inp.threshold is not None else data_settings.VECTOR_SEARCH_THRESHOLD

        video_search_results = weviate_client.search(
            text=text, 
            speaker_id=speaker_id,
            alpha=search_alpha,
            limit=3
            )
        
        self.logger.info(f"Search results: {video_search_results}")

        session_id = str(uuid.uuid4())

        # Set redis status
        await self.redis_client.set(
            session_id,
            json.dumps({
                "status": "STARTED",
                "local_path": "",
                "remote_path": ""
            })
        )

        if (
            (len(video_search_results) == 0) or 
            (
                (video_search_results[0]['score'] is not None) and 
                (video_search_results[0]['score'] != 0) and 
                (video_search_results[0]['score'] < search_threshold)
            ) or
            (
                (video_search_results[0]['distance'] is not None) and 
                (video_search_results[0]['distance'] != 0) and 
                (video_search_results[0]['distance'] >= search_threshold)
            )
            ):
            ''' Generating if the video is not found '''
            video_resp = await self.generate_video(text=text, speaker_id=speaker_id, session_id=session_id)

            weviate_client.insert(
                text=text,
                speaker_id=speaker_id,
                video_path=video_resp["output_path"],
            )
        else:
            updated_session = {
                "status": "SUCCESS",
                "local_path": "",
                "remote_path": video_search_results[0]['properties']['video_path']
            }
            
            await self.redis_client.set(session_id, json.dumps(updated_session))

        weviate_client.close()

        report_res = []
        if video_search_results:
            for res in video_search_results:
                report_res.append([res['properties']['text'], res['distance'], res['score']])

        return JSONResponse(content={"session_id": session_id, "search_results": report_res})

    @app.get("/video")
    async def stream(self, session_id) -> GetGenerationStatus:
        session_data = await self.redis_client.get(session_id)

        if session_data is None:
            raise HTTPException(status_code=404, detail="Session not found")

        session = json.loads(session_data)

        return GetGenerationStatus(
            status=session["status"],
            message=session["remote_path"]
            )
    
    async def generate_video(self, text:str, speaker_id:str, session_id:str) -> str:
        image_path = INTERVIEWER_AVATAR.get(speaker_id, INTERVIEWER_AVATAR["random"])
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Call TTS service
        audio_base64: str = await self.tts.remote(text, speaker_id)
        audio_bytes = base64.b64decode(audio_base64)

        # Call SadTalker
        video_gen_resp: dict = await self.sadtalker.remote(audio_bytes, image_bytes, session_id)

        return video_gen_resp
