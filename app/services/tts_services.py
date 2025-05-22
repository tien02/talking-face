from src.tts_engine import IndianTextToSpeech, IndianTextToSpeechInput
from ray import serve

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 2, "num_gpus":1})
class IndianTextToSpeechDeployment:
    def __init__(self):
        self.tts = IndianTextToSpeech()

    async def __call__(self, text: str, speaker_id: str = "random"):
        request = IndianTextToSpeechInput(text=text, speaker_id=speaker_id)
        response = self.tts(request)
        return response.audio_base64
    