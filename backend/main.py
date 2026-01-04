import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from storage.cache import get_cached_result, save_cached_result
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from graph.pipeline import build_pipeline
from agents.langgraph_nodes import init_agents
from database import engine, Base, get_db
from models import User
from auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from models import User, Video
from datetime import datetime

Base.metadata.create_all(bind=engine)

class PromptRequest(BaseModel):
    prompt: str

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

app = FastAPI(title="Animathics", version="2.0-agentic")

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

agents = init_agents(
    gemini_model,
    elevenlabs_client,
    AUDIO_DIR
)

pipeline = build_pipeline(agents)

@app.get("/")
def health_check():
    return {
        "status": "running",
        "mode": "langgraph-agentic",
        "agents": list(agents.keys())
    }

# @app.post("/generate-video")
# def generate_video(req: PromptRequest):
#     initial_state = {
#         "prompt": req.prompt,
#         "manim_code": None,
#         "transcript": f"Explaining {req.prompt}",
#         "script_path": None,
#         "video_path": None,
#         "audio_path": None,
#         "audio_script": None,
#         "error": None,
#         "retries": 0,
#         "scripts_dir": SCRIPTS_DIR,
#         "videos_dir": VIDEOS_DIR,
#     }

#     result = pipeline.invoke(initial_state)

#     if result.get("error"):
#         raise HTTPException(status_code=500, detail=result["error"])

#     return {
#         "videoUrl": f"http://localhost:8000/videos/{os.path.basename(result['final_video_path'])}",
#         "audioUrl": (
#             f"http://localhost:8000/audio/{os.path.basename(result['audio_path'])}"
#             if result.get("audio_path") else None
#         )
#     }

@app.post("/generate-video")
def generate_video(
    req: PromptRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)                   
):
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

    video_file = result.get("final_video_path") or result.get("video_path")

    if not video_file or not os.path.exists(video_file):
        raise HTTPException(status_code=500, detail="Video generation failed.")

    new_video = Video(
        user_id=current_user.id,
        prompt=req.prompt,
        video_filename=os.path.basename(video_file),
        audio_filename=os.path.basename(result["audio_path"]) if result.get("audio_path") else None
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    response = {
        "videoUrl": f"http://localhost:8000/videos/{new_video.video_filename}",
        "audioUrl": None,
        "prompt": new_video.prompt,
        "timestamp": new_video.created_at
    }

    if new_video.audio_filename:
        response["audioUrl"] = f"http://localhost:8000/audio/{new_video.audio_filename}"
    
    return response

@app.get("/api/history") 
def get_video_history(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    videos = db.query(Video).filter(Video.user_id == current_user.id).order_by(Video.created_at.desc()).all()
    
    history = []
    for vid in videos:
        history.append({
            "videoUrl": f"http://localhost:8000/videos/{vid.video_filename}",
            "prompt": vid.prompt,
            "timestamp": vid.created_at
        })
    return history

@app.post("/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "session_id": current_user.session_id  
    }

@app.get("/chat/history/{session_id}")
def get_chat_history(session_id: str):
    history = get_cached_result(f"chat_{session_id}")
    return history if history else []

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    history_key = f"chat_{session_id}"
    existing_history = get_cached_result(history_key) or []
    
    gemini_history = []
    for msg in existing_history:
        gemini_history.append({
            "role": msg["role"],
            "parts": [msg["content"]]
        })

    tutor_model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        system_instruction="You are a helpful math tutor. Explain concepts clearly."
    )
    chat_session = tutor_model.start_chat(history=gemini_history)

    try:
        while True:
            user_input = await websocket.receive_text()
            
            existing_history.append({"role": "user", "content": user_input})
            save_cached_result(history_key, existing_history)

            response_stream = await chat_session.send_message_async(user_input, stream=True)
            
            full_response = ""
            async for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    await websocket.send_text(chunk.text)
            
            await websocket.send_text("")

            existing_history.append({"role": "model", "content": full_response})
            save_cached_result(history_key, existing_history)

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
