import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from pydantic import BaseModel

from agents.gemini_manim_agent import GeminiManimAgent
from agents.alignment_agent import AlignmentAgent
from agents.audio_agent import AudioAgent
from orchestrator.video_orchestrator import VideoOrchestrator

load_dotenv()

class PromptRequest(BaseModel):
    prompt: str

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEOS_DIR = "videos"
AUDIO_DIR = "audio"
SCRIPTS_DIR = "temp_scripts"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)

app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Agents
manim_agent = GeminiManimAgent(gemini_model)
align_agent = AlignmentAgent(gemini_model)
audio_agent = AudioAgent(elevenlabs_client, AUDIO_DIR)

orchestrator = VideoOrchestrator(
    manim_agent,
    align_agent,
    audio_agent,
    SCRIPTS_DIR,
    VIDEOS_DIR
)

@app.post("/generate-video")
def generate_video(req: PromptRequest):
    result = orchestrator.run(req.prompt)
    if not result.success:
        raise HTTPException(500, result.error)

    return {
        "videoUrl": f"http://localhost:8000/videos/{os.path.basename(result.data)}"
    }
