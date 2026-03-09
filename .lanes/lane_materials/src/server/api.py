from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.graph_orchestrator import GraphOrchestrator
# from config import Config

app = FastAPI(title="ResearchBot Headless API")

# --- State Management ---
class BotState:
    orchestrator: GraphOrchestrator = None
    running: bool = False
    latest_logs: list = []
    current_node: str = "Idle"
    waiting_for_input: bool = False

bot_state = BotState()

# --- Schemas ---
class ResearchRequest(BaseModel):
    topic: str
    mode: str = "standard"  # standard, theory_first, autonomous

class ReviewRequest(BaseModel):
    decision: str  # Approve, Reject, Terminate
    feedback: str = ""

# --- Dependency Injection ---
async def get_orchestrator():
    if not bot_state.orchestrator:
        # Initialize Core
        bot_state.orchestrator = GraphOrchestrator()
        # Mock initialization or real dependent on design
    return bot_state.orchestrator

# --- Background Worker ---
async def run_agent_loop(topic: str, mode: str):
    bot_state.running = True
    bot_state.logs = []
    try:
        orch = await get_orchestrator()
        
        # We need to adapt run_autonomous to be non-blocking or just await it here in this thread
        # ideally GraphOrchestrator.run_autonomous is async, so we just await it.
        # But we need to capture logs. 
        # For now, we assume RichLogger writes to stdout/file, and we might implement a log sniffer later.
        
        initial_state = {
            "topic": topic,
            "research_mode": mode,
            "autonomous_mode": True if mode == "autonomous" else False
        }
        
        # This will block this worker until finished or interrupted
        final_state = await orch.run_cycle(topic)
        bot_state.running = False
        bot_state.current_node = "Done"
        
    except Exception as e:
        bot_state.running = False
        bot_state.current_node = f"Error: {str(e)}"

# --- Endpoints ---

@app.post("/api/v1/research/start")
async def start_research(req: ResearchRequest, background_tasks: BackgroundTasks):
    if bot_state.running:
        return {"status": "error", "message": "Bot is already running"}
    
    background_tasks.add_task(run_agent_loop, req.topic, req.mode)
    return {"status": "started", "topic": req.topic, "mode": req.mode}

@app.get("/api/v1/research/status")
async def get_status():
    return {
        "running": bot_state.running,
        "current_node": bot_state.current_node,
        "waiting_for_input": bot_state.waiting_for_input,
        # "latest_logs": bot_state.latest_logs[-10:] # Todo: Connect rich logger
    }

@app.post("/api/v1/human/review")
async def submit_review(req: ReviewRequest):
    # This endpoint mimics the "Human Review Node" input
    # In LangGraph, we need to update the state or resume execution.
    # Current GraphOrchestrator might need a mechanism to inject this.
    # For now, we log it, assuming the Orchestrator polls or we hack the state.
    
    # Ideally: bot_state.orchestrator.inject_human_feedback(req.decision)
    return {"status": "received", "decision": req.decision}

@app.get("/")
def read_root():
    return {"message": "ResearchBot API is Active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
