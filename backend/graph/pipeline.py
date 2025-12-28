from langgraph.graph import StateGraph, END
from graph.pipeline_state import PipelineState
from agents.langgraph_nodes import fix_node, media_sync_node
from agents.langgraph_nodes import (
    gemini_node,
    alignment_node,
    save_script_node,
    test_node,
    render_node,
    audio_node,
)

def route_after_test(state):
    # 1. Success! -> Run Render and Audio in Parallel
    if state.get("test_passed"):
        return ["render", "audio"]

    # 2. Fixable Error: We have an error AND code exists AND retries left
    if (state.get("error") and 
        state.get("manim_code") and 
        state.get("retries", 0) < 2):
        return "fix"

    # 3. Critical Failure (No code generated) or Max Retries
    return "end"

def build_pipeline(agents):
    graph = StateGraph(PipelineState)

    # Add Nodes
    graph.add_node("gemini", lambda s: gemini_node(s, agents))
    graph.add_node("align", lambda s: alignment_node(s, agents))
    graph.add_node("save_script", lambda s: save_script_node(s, agents))
    graph.add_node("test", lambda s: test_node(s, agents))
    graph.add_node("render", lambda s: render_node(s, agents))
    graph.add_node("audio", lambda s: audio_node(s, agents))
    graph.add_node("fix", lambda s: fix_node(s, agents))
    graph.add_node("media_sync", lambda s: media_sync_node(s, agents))

    # Set Entry Point
    graph.set_entry_point("gemini")

    # Sequential Flow (Generation)
    graph.add_edge("gemini", "align")
    graph.add_edge("align", "save_script")
    graph.add_edge("save_script", "test")

    # Conditional Branching
    graph.add_conditional_edges(
        "test",
        route_after_test,
        {
            "render": "render",
            "audio": "audio",
            "fix": "fix",
            "end": END,
        }
    )

    # Fix Loop
    graph.add_edge("fix", "save_script")

    # Parallel Convergence
    # Both render and audio must finish; StateGraph handles the merge,
    # then proceeds to media_sync in the next step.
    graph.add_edge("render", "media_sync")
    graph.add_edge("audio", "media_sync")
    
    # Final Step
    graph.add_edge("media_sync", END)

    return graph.compile()