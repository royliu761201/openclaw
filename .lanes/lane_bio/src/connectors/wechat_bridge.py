
import asyncio
import time
import requests
import json
from rich.console import Console

# Mock ItChat for skeleton
# In production, import itchat
# @itchat.msg_register(itchat.content.TEXT)

API_BASE = "http://localhost:8000/api/v1"
console = Console()

class WeChatBridge:
    def __init__(self):
        self.user_whitelist = ["Researcher_Roy"]
        
    def handle_message(self, sender: str, content: str):
        """
        Maps WeChat messages to API calls.
        """
        console.print(f"[WeChat] Received from {sender}: {content}")
        
        args = content.split()
        command = args[0].lower()
        
        if command == "start":
            # Format: start <topic> <mode>
            topic = " ".join(args[1:-1]) if len(args) > 2 else "Deep Learning"
            mode = args[-1] if args[-1] in ["standard", "autonomous"] else "standard"
            
            try:
                res = requests.post(f"{API_BASE}/research/start", json={"topic": topic, "mode": mode})
                return f"Bot Started! Topic: {topic}, Mode: {mode}. Status: {res.json()}"
            except Exception as e:
                return f"Error starting bot: {e}"
                
        elif command == "status":
            try:
                res = requests.get(f"{API_BASE}/research/status")
                data = res.json()
                return f"Status: {'Running' if data['running'] else 'Idle'}\nNode: {data['current_node']}"
            except:
                return "Error fetching status."
                
        elif command == "approve":
            requests.post(f"{API_BASE}/human/review", json={"decision": "Approve"})
            return "✅ Proposal Approved. Continuing..."
            
        elif command == "reject":
            requests.post(f"{API_BASE}/human/review", json={"decision": "Reject"})
            return "❌ Proposal Rejected. Regenerating..."
            
        return "Unknown Command. Try: start, status, approve, reject"

    async def run_loop(self):
        print("[Bridge] WeChat Bridge listening (Mock Mode)...")
        # In real life, itchat.run() blocks. 
        # Here we mock a loop that inputs from stdin for demo
        while True:
            cmd = await asyncio.to_thread(input, "Enter Simulated WeChat Msg: ")
            reply = self.handle_message("Researcher_Roy", cmd)
            print(f"[Bridge] Reply: {reply}")

if __name__ == "__main__":
    bridge = WeChatBridge()
    asyncio.run(bridge.run_loop())
