import os
from elevenlabs.client import ElevenLabs
from io import BytesIO

class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_KEY"))

    def stream_audio(self, text_stream):
        # Placeholder for TTS
        pass

    def transcribe_audio(self, audio_data):
        """
        Transcribe audio data (bytes) using ElevenLabs Scribe.
        """
        try:
            # Create a file-like object from bytes
            audio_file = BytesIO(audio_data)
            audio_file.name = "recording.webm"  # Help ElevenLabs identify format
            
            transcription = self.client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v2",
                tag_audio_events=False,  # Disable to simplify response
                language_code="eng",
                diarize=False  # Disable speaker diarization to simplify
            )
            return transcription
        except Exception as e:
            print(f"ElevenLabs STT Error: {e}")
            return None
