import os

# -------------------- FastAPI --------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# -------------------- ENV --------------------
from dotenv import load_dotenv

# -------------------- AI SDKs --------------------
import google.generativeai as genai
from elevenlabs.client import ElevenLabs

# -------------------- LangGraph --------------------
from graph.pipeline import build_pipeline
from agents.langgraph_nodes import init_agents

# -------------------- Load ENV --------------------
load_dotenv()

# -------------------- Request Schema --------------------
class PromptRequest(BaseModel):
    prompt: str

# -------------------- API Keys --------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY not found")

# -------------------- Models --------------------
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# -------------------- FastAPI App --------------------
app = FastAPI(title="Animathics", version="2.0-agentic")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Directories --------------------
VIDEOS_DIR = "videos"
AUDIO_DIR = "audio"
SCRIPTS_DIR = "temp_scripts"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)

app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# -------------------- Init Agents --------------------
agents = init_agents(
    gemini_model,
    elevenlabs_client,
    AUDIO_DIR
)


# -------------------- Build LangGraph Pipeline --------------------
pipeline = build_pipeline(agents)

# -------------------- Routes --------------------
@app.get("/")
def health_check():
    return {
        "status": "running",
        "mode": "langgraph-agentic",
        "agents": list(agents.keys())
    }

@app.post("/generate-video")
def generate_video(req: PromptRequest):
    initial_state = {
        "prompt": req.prompt,
        "manim_code": None,
        "transcript": f"Explaining {req.prompt}",
        "script_path": None,
        "video_path": None,
        "audio_path": None,
        "audio_script": None,
        "error": None,
        "retries": 0,
        "scripts_dir": SCRIPTS_DIR,
        "videos_dir": VIDEOS_DIR,
    }


    result = pipeline.invoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "videoUrl": f"http://localhost:8000/videos/{os.path.basename(result['final_video_path'])}",
        "audioUrl": (
            f"http://localhost:8000/audio/{os.path.basename(result['audio_path'])}"
            if result.get("audio_path") else None
        )
    }
