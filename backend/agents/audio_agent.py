import uuid, os
from agents.base import BaseAgent, AgentResult
from elevenlabs import save

class AudioAgent(BaseAgent):
    name = "AudioAgent"

    def __init__(self, elevenlabs_client, audio_dir):
        self.client = elevenlabs_client
        self.audio_dir = audio_dir

    def run(self, text: str) -> AgentResult:
        try:
            audio = self.client.text_to_speech.convert(
                voice_id="21m00Tcm4TlvDq8ikWAM",
                model_id="eleven_multilingual_v2",
                text=text
            )
            fname = f"audio_{uuid.uuid4().hex}.mp3"
            path = os.path.join(self.audio_dir, fname)
            save(audio, path)
            return AgentResult(True, path)
        except Exception as e:
            return AgentResult(False, error=str(e))
