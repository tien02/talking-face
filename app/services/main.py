import ray
from ray import serve
from ray.serve.config import HTTPOptions

from .tts_services import IndianTextToSpeechDeployment
from .video_services import SadTalkerDeployment
from .e2e_services import VideoGenerator

serve.start(http_options=HTTPOptions(host="0.0.0.0", port=8091))

tts_app = IndianTextToSpeechDeployment.bind()
talkinghead_app = SadTalkerDeployment.bind()
ava_gen_app = VideoGenerator.bind(tts_app, talkinghead_app)
serve.run(ava_gen_app)