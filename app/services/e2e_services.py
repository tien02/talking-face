import uuid
import base64
import asyncio
import aiofiles

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from ray import serve
from ray.serve.handle import DeploymentHandle

from aiortc.contrib.media import MediaPlayer
from aiortc import RTCPeerConnection, RTCSessionDescription

from typing import Dict
from schemas.app import GenerationRequest, StreamRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pcs = set() 
CHUNK_SIZE = 1024 * 1024
video_sessions: Dict[str, Dict] = {}

@serve.deployment(ray_actor_options={"num_cpus": 0.5})
@serve.ingress(app)
class VideoGenerator:
    def __init__(self, tts_handle: DeploymentHandle, sadtalker_handle: DeploymentHandle):
        self.tts = tts_handle
        self.sadtalker = sadtalker_handle
    
    async def aiofiles_iterator(self, filepath: str):
        async with aiofiles.open(filepath, 'rb') as file:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

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

        return StreamingResponse(self.aiofiles_iterator(video_path), media_type="video/mp4")

    @app.post("/generate-stream")
    async def generate_stream(self, request: GenerationRequest):
        text = request.text
        speaker_id = request.speaker_id
        image_bytes = base64.b64decode(request.image_bytes)

        session_id = str(uuid.uuid4())
        video_path = f"/tmp/{session_id}.mp4"
        video_sessions[session_id] = {
            "status": "processing",
            "video_path": video_path
        }

        async def run_generation():
            try:
                audio_base64: str = await self.tts.remote(text, speaker_id)
                audio_bytes = base64.b64decode(audio_base64)

                video_response: dict = await self.sadtalker.remote(audio_bytes, image_bytes)
                video_sessions[session_id]["video_path"] = video_response.output_video
                video_sessions[session_id]["status"] = "ready"
            except Exception as e:
                video_sessions[session_id]["status"] = "failed"
                print(f"Generation failed for {session_id}: {e}")

        asyncio.create_task(run_generation())

        return JSONResponse({"session_id": session_id})

    @app.post("/stream")
    async def stream(self, stream_request: StreamRequest):
        session_id = stream_request.session_id
        if session_id not in video_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Poll for readiness
        for _ in range(60):
            session = video_sessions[session_id]
            if session["status"] == "ready":
                break
            elif session["status"] == "failed":
                raise HTTPException(status_code=500, detail="Generation failed")
            await asyncio.sleep(0.5)
        else:
            raise HTTPException(status_code=504, detail="Timeout: video not ready")

        video_path = video_sessions[session_id]["video_path"]

        pc = RTCPeerConnection()
        pcs.add(pc)  # optional if you maintain a set of connections

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if pc.connectionState == "failed":
                await pc.close()
                pcs.discard(pc)

        # Directly stream video file without any transform
        player = MediaPlayer(video_path)

        if player.video:
            pc.addTrack(player.video)
        if player.audio:
            pc.addTrack(player.audio)
        
        async def close_when_done():
            while True:
                if player.audio and player.audio.readyState == "ended" and \
                player.video and player.video.readyState == "ended":
                    break
                await asyncio.sleep(0.5)
            await pc.close()
            pcs.discard(pc)
            await player.stop()

        asyncio.create_task(close_when_done())

        offer = RTCSessionDescription(sdp=stream_request.sdp, type=stream_request.type)
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return JSONResponse({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })
