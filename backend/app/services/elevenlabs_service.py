import os
from elevenlabs.client import ElevenLabs
from io import BytesIO

class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_KEY"))

    def stream_audio(self, text):
        """
        Convert text to speech using ElevenLabs TTS.
        Returns audio bytes that can be streamed to frontend.
        """
        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id="JBFqnCBsd6RMkjVDRZzb",  # George - calm, soothing voice
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            return audio_bytes
        except Exception as e:
            print(f"ElevenLabs TTS Error: {e}")
            return None

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
