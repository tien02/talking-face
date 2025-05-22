import time
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf


import io
import base64
from config.voice import audio_settings
from schemas.voice import IndianTextToSpeechInput, IndianTextToSpeechResponse
from common.voice import VOICE_DESCRIPTIONS

class IndianTextToSpeech:
    def __init__(self):
        self._model = ParlerTTSForConditionalGeneration.from_pretrained(
            audio_settings.VOICE_MODEL_NAME_OR_PATH,
            attn_implementation=audio_settings.VOICE_ATTN_IMPLEMENTATION
        ).to(audio_settings.VOICE_DEVICE)
        self._tokenizer = AutoTokenizer.from_pretrained(audio_settings.VOICE_MODEL_NAME_OR_PATH)
        self._description_tokenizer = AutoTokenizer.from_pretrained(self._model.config.text_encoder._name_or_path)

    def __call__(self, request: IndianTextToSpeechInput) -> IndianTextToSpeechResponse:
        description = self._get_description(speaker_id=request.speaker_id)
        prompt = request.text

        if len(prompt) == 0:
            return IndianTextToSpeechResponse()
        
        description_input_ids = self._description_tokenizer(description, return_tensors="pt").to(audio_settings.VOICE_DEVICE)
        prompt_input_ids = self._tokenizer(prompt, return_tensors="pt").to(audio_settings.VOICE_DEVICE)

        start_time = time.time()
        generation = self._model.generate(
            input_ids=description_input_ids.input_ids, 
            attention_mask=description_input_ids.attention_mask, 
            prompt_input_ids=prompt_input_ids.input_ids, 
            prompt_attention_mask=prompt_input_ids.attention_mask
        )
        end_time = time.time()

        audio_arr = generation.cpu().numpy().squeeze()
        generate_time = end_time - start_time
        audio_duration = audio_arr.shape[0] / self._model.config.sampling_rate 
        rtf = generate_time / audio_duration if audio_duration > 0 else float('inf')

        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, self._model.config.sampling_rate, format="wav")
        audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return IndianTextToSpeechResponse(
            audio_base64=audio_base64,
            generate_time=generate_time,
            rtf=rtf,
            duration=audio_duration
        )

    def _get_description(self, speaker_id:str) -> str:
        description = VOICE_DESCRIPTIONS.get(speaker_id, None)
        if description is None:
            description = VOICE_DESCRIPTIONS['random']
        
        return description
