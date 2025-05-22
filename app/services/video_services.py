import base64
from ray import serve
from src.video_engine import SadTalkerAnimator, SadTalkerAnimatorInput, SadTalkerAnimatorResponse

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 4, "num_gpus": 1})
class SadTalkerDeployment:
    def __init__(self):
        self.animator = SadTalkerAnimator()

    async def __call__(self, audio_bytes: bytes, image_bytes: bytes) -> SadTalkerAnimatorResponse:
        audio_path = "/tmp/audio.wav"
        image_path = "/tmp/image.png"
        with open(audio_path, "wb") as f: f.write(audio_bytes)
        with open(image_path, "wb") as f: f.write(image_bytes)

        animator_inp = SadTalkerAnimatorInput(driven_audio=audio_path, source_image=image_path)

        video_response = self.animator(animator_inp)

        return video_response
        
