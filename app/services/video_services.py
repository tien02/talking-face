import os
import uuid
import json
import asyncio
import logging

from ray import serve
from redis.asyncio import Redis
from fastapi.responses import JSONResponse

from config.data import data_settings
from src.data.minio import MinioClient
from src.video_engine import SadTalkerAnimator, SadTalkerAnimatorInput, SadTalkerAnimatorResponse

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 4, "num_gpus": 1})
class SadTalkerDeployment:
    def __init__(self):
        self.animator = SadTalkerAnimator()
        self.redis_client = Redis(
            host=data_settings.REDIS_HOST,
            port=data_settings.REDIS_PORT,
            db=data_settings.REDIS_DB
        )
        self.minio_client = MinioClient()
        self.logger = logging.getLogger("ray")

    async def __call__(
            self, 
            audio_bytes: bytes, 
            image_bytes: bytes, 
        ):
        uid = str(uuid.uuid4())
        audio_path = f"/tmp/audio_{uid}.wav"
        image_path = f"/tmp/image_{uid}.png"
        with open(audio_path, "wb") as f: f.write(audio_bytes)
        with open(image_path, "wb") as f: f.write(image_bytes)

        session_id = str(uuid.uuid4())
        output_path = os.path.join(data_settings.MINIO_BUCKET, f"{session_id}.mp4")

        # Set redis status
        await self.redis_client.set(
            session_id,
            json.dumps({
                "status": "STARTED",
                "local_path": "",
                "remote_path": ""
            })
        )

        # Run the generation in background
        async def run_generation():
            try:
                animator_inp = SadTalkerAnimatorInput(driven_audio=audio_path, source_image=image_path)
                video_response:SadTalkerAnimatorResponse = self.animator(animator_inp)

                # Upload to MinIO
                parts = output_path.split('/', 1)
                bucket_name = parts[0]
                object_name = parts[1] if len(parts) > 1 else ""

                self.minio_client.upload(
                    bucket_name=bucket_name, 
                    local_path=video_response.output_video, 
                    remote_path=object_name, 
                    content_type="video/mp4"
                )

                # Update status
                updated_session = {
                    "status": "SUCCESS",
                    "local_path": video_response.output_video,
                    "remote_path": output_path
                }
            except Exception as e:
                self.logger.info(f"Error: {str(e)}")
                updated_session = {
                    "status": f"FAIL: {e}",
                    "local_path": "",
                    "remote_path": ""
                }

            
            await self.redis_client.set(session_id, json.dumps(updated_session))

        asyncio.create_task(run_generation())

        return JSONResponse(content={"session_id": session_id})
