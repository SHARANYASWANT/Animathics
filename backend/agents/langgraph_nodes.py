import os
import uuid
from graph.pipeline_state import PipelineState

# ---------------- INIT AGENTS ----------------

def init_agents(gemini_model, eleven_client, audio_dir):
    from agents.gemini_manim_agent import GeminiManimAgent
    from agents.alignment_agent import AlignmentAgent
    from agents.test_agent import TestAgent
    from agents.render_agent import RenderAgent
    from agents.audio_agent import AudioAgent
    from agents.fix_agent import FixAgent
    from agents.media_sync_agent import MediaSyncAgent

    return {
        "gemini": GeminiManimAgent(gemini_model),
        "align": AlignmentAgent(gemini_model),
        "test": TestAgent(),
        "render": RenderAgent(),
        "audio": AudioAgent(eleven_client, audio_dir),
        "fix": FixAgent(gemini_model),
        "media_sync": MediaSyncAgent(),
    }

# ---------------- GRAPH NODES ----------------

def gemini_node(state: PipelineState, agents):
    result = agents["gemini"].run(state["prompt"])

    if not result.success:
        return {
            "error": result.error,
            "manim_code": None
        }

    return {
        "manim_code": result.data["manim_code"],
        "audio_script": result.data["audio_script"],
        "error": None
    }


def fix_node(state, agents):
    result = agents["fix"].run(state)

    if not result.success:
        return {
            "error": result.error,
            "retries": state.get("retries", 0) + 1
        }

    return {
        "manim_code": result.data,
        "retries": state.get("retries", 0) + 1,
        "error": None
    }


def alignment_node(state: PipelineState, agents):
    # If error exists, return empty dict (no updates)
    if state.get("error"):
        return {}

    result = agents["align"].run(state["manim_code"])
    
    # Only update manim_code if successful
    if result.success:
        return {"manim_code": result.data}
    
    return {}


def save_script_node(state, agents):
    if state.get("error"):
        return {}

    if not state.get("manim_code"):
        return {"error": "No Manim code generated"}

    scripts_dir = state["scripts_dir"]
    os.makedirs(scripts_dir, exist_ok=True)

    script_name = f"video_{uuid.uuid4().hex}.py"
    script_path = os.path.join(scripts_dir, script_name)

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(state["manim_code"])

    return {
        "script_path": script_path,
        "error": None
    }

def test_node(state, agents):
    if state.get("error"):
        return {}

    script_path = state.get("script_path")
    if not script_path:
        return {"error": "Script path is missing"}

    result = agents["test"].run(script_path)

    if result.success:
        return {
            "error": None,
            "test_passed": True
        }

    # If retries maxed out
    if state.get("retries", 0) >= 2:
        return {
            "error": "Max retries reached during test",
            "test_passed": False
        }

    return {"error": "Test failed, requesting fix"}

def render_node(state: PipelineState, agents):
    # Parallel Node: MUST only return its specific updates
    if state.get("error"):
        return {}

    result = agents["render"].run(
        state["script_path"],
        state["videos_dir"]
    )
    if not result.success:
        return {"error": result.error}

    return {"video_path": result.data}


def audio_node(state: PipelineState, agents):
    # Parallel Node: MUST only return its specific updates
    if state.get("error"):
        return {}

    script = state.get("audio_script")
    if not script:
        return {"error": "No audio script found"}

    result = agents["audio"].run(script)
    if result.success:
        return {"audio_path": result.data}
    
    return {"error": result.error}

def media_sync_node(state: PipelineState, agents):
    if state.get("error"):
        return {}

    if not state.get("video_path") or not state.get("audio_path"):
        return {"error": "Missing audio or video for merging"}

    result = agents["media_sync"].run(
        state["video_path"],
        state["audio_path"],
        state["videos_dir"]
    )

    if not result["success"]:
        return {"error": result["error"]}

    return {
        "final_video_path": result["data"]
    }