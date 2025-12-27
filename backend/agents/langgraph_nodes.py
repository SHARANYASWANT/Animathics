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

    return {
        "gemini": GeminiManimAgent(gemini_model),
        "align": AlignmentAgent(gemini_model),
        "test": TestAgent(),
        "render": RenderAgent(),
        "audio": AudioAgent(eleven_client, audio_dir),
        "fix": FixAgent(gemini_model)
    }

def merge_state(old, updates):
    return {**old, **updates}


# ---------------- GRAPH NODES ----------------

def gemini_node(state: PipelineState, agents):
    # 1. Run Gemini
    result = agents["gemini"].run(state["prompt"])
    
    # 2. Check for failure
    if not result.success:
        # Return the ACTUAL error from Gemini (e.g., API key issue)
        return merge_state(state, {
            "error": result.error or "Gemini returned empty code",
            "manim_code": None
        })

    return merge_state(state, {
        "manim_code": result.data,
        "error": None
    })

def fix_node(state, agents):
    # This calls the FixAgent class we just created
    result = agents["fix"].run(state)

    if not result.success:
        return merge_state(state, {
            "error": result.error,
            "retries": state["retries"] + 1
        })

    return merge_state(state, {
        "manim_code": result.data,
        "retries": state["retries"] + 1,
        "error": None
    })


def alignment_node(state: PipelineState, agents):
    # 1. Skip if there is already an error
    if state.get("error"):
        return state

    # 2. Run Alignment
    result = agents["align"].run(state["manim_code"])
    
    return merge_state(state, {
        "manim_code": result.data if result.success else state["manim_code"]
    })


def save_script_node(state, agents):
    # 1. Check for upstream error first!
    if state.get("error"):
        return {"error": state["error"]}

    # 2. Check if code exists
    if not state.get("manim_code"):
        return merge_state(state, {"error": "No Manim code generated (Check Gemini API key)"})

    scripts_dir = state["scripts_dir"]
    os.makedirs(scripts_dir, exist_ok=True)

    script_name = f"video_{uuid.uuid4().hex}.py"
    script_path = os.path.join(scripts_dir, script_name)

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(state["manim_code"])

    return merge_state(state, {
        "script_path": script_path,
        "error": None
    })

def test_node(state, agents):
    # 1. Safety Check: If previous steps failed, don't run test
    if state.get("error"):
        return {"error": state["error"]}

    script_path = state.get("script_path")
    if not script_path:
        return {"error": "Script path is missing (Generation failed)"}

    # 2. Run the test
    result = agents["test"].run(script_path)

    if result.success:
        return {
            "error": None,
            "test_passed": True
        }

    # 3. Handle Failure
    # If we have retried enough times, stop (return error without fix request)
    if state.get("retries", 0) >= 2:
        return {
            "error": "Max retries reached during test",
            "test_passed": False
        }

    # IMPORTANT: Set an error string here. 
    # The router sees this error + retries < 2, and sends it to 'fix'.
    return merge_state(state, {"error": "Test failed, requesting fix"})

def render_node(state: PipelineState, agents):
    result = agents["render"].run(
        state["script_path"],
        state["videos_dir"]
    )
    if not result.success:
        return merge_state(state, {"error": result.error})

    return merge_state(state, {"video_path": result.data})


def audio_node(state: PipelineState, agents):
    result = agents["audio"].run(state["transcript"])
    if result.success:
        return merge_state(state, {"audio_path": result.data})
    return merge_state(state, {})
