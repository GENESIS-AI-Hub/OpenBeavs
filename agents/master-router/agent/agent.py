
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import os
import json
import httpx
import asyncio
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Configuration
OPENWEBUI_URL = os.environ.get("OPENWEBUI_URL", "http://localhost:8080")
OPENWEBUI_API_KEY = os.environ.get("OPENWEBUI_API_KEY", "")
AGENT_CACHE_REFRESH_SECONDS = int(os.environ.get("AGENT_CACHE_REFRESH_SECONDS", "30"))

# ─── Cached agents list ───────────────────────────────────────────────
# Fetched on startup and refreshed every N seconds in a background thread.
# This avoids a circular deadlock: Open WebUI (single-worker) → Master Router
# → back to Open WebUI would hang because the single worker is already busy.
_cached_agents: list = []
_cache_lock = threading.Lock()


def _refresh_agents_cache():
    """Fetch agents from Open WebUI and update the cache."""
    global _cached_agents
    try:
        headers = {
            "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
            "Content-Type": "application/json",
        }
        response = httpx.get(
            f"{OPENWEBUI_URL}/api/v1/agents/user-agents",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        agents = response.json()
        with _cache_lock:
            _cached_agents = agents
        print(f"[Router] Cache refreshed: {len(agents)} agents found")
    except Exception as e:
        print(f"[Router] Cache refresh failed: {type(e).__name__}: {e}")


def _cache_refresh_loop():
    """Background thread that periodically refreshes the agents cache."""
    while True:
        _refresh_agents_cache()
        time.sleep(AGENT_CACHE_REFRESH_SECONDS)


# Start the background cache refresh thread
_cache_thread = threading.Thread(target=_cache_refresh_loop, daemon=True)
_cache_thread.start()


# ─── Tool functions ───────────────────────────────────────────────────

def get_user_agents() -> dict:
    """Fetch all agents that are currently installed and available in the GENESIS AI Hub.
    
    Returns a dictionary containing a list of available agents, each with their
    id, name, description, skills, capabilities, and endpoint.
    Use this tool FIRST before deciding how to route the user's message.
    """
    with _cache_lock:
        agents = list(_cached_agents)
    
    # Filter out this router agent itself
    agents = [a for a in agents if a.get("name", "").lower() != "master router"]
    
    print(f"[Router] get_user_agents called — returning {len(agents)} agents from cache")
    
    if not agents:
        return {"agents": [], "message": "No specialist agents are currently installed. Answer the user's question directly."}
    
    return {"agents": agents}


async def route_to_agent(agent_endpoint: str, message: str) -> dict:
    """Send a message to a specific specialist agent via A2A protocol and return its response.
    
    Args:
        agent_endpoint: The full URL endpoint of the agent to route to (from get_user_agents results).
        message: The user's original message to forward to the specialist agent.
    
    Returns a dictionary with the agent's response text.
    """
    import uuid
    
    try:
        agent_endpoint = agent_endpoint.rstrip("/")
        
        message_id = str(uuid.uuid4())
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "messageId": message_id,
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"text": message}],
                },
            },
            "id": 1,
        }
        
        print(f"[Router] Routing to agent at {agent_endpoint}")
        response_data = await asyncio.to_thread(
            lambda: httpx.post(agent_endpoint, json=jsonrpc_request, timeout=60).json()
        )
        
        # Extract response text from A2A JSON-RPC result
        result = response_data.get("result", {})
        response_text = ""
        
        # A2A format: result.artifacts[0].parts[0].text
        if isinstance(result, dict) and "artifacts" in result:
            artifacts = result.get("artifacts", [])
            if artifacts:
                parts = artifacts[0].get("parts", [])
                if parts:
                    response_text = parts[0].get("text", "")
        
        # Fallback formats
        if not response_text and isinstance(result, dict):
            parts = result.get("parts", [])
            if parts and isinstance(parts, list):
                response_text = parts[0].get("text", str(result))
            else:
                response_text = result.get("text", str(result))
        elif not response_text:
            response_text = str(result)
        
        print(f"[Router] Got response from agent ({len(response_text)} chars)")
        return {"response": response_text, "routed_to": agent_endpoint}
    
    except Exception as e:
        return {"error": f"Failed to communicate with agent at {agent_endpoint}: {str(e)}"}


# ─── Agent definition ────────────────────────────────────────────────

router_agent = Agent(
    name="master_router",
    model=os.environ.get("ROUTER_MODEL", "gemini-2.0-flash"),
    tools=[get_user_agents, route_to_agent],
    description=(
        "The Master Router Agent for GENESIS AI Hub. "
        "Intelligently routes user conversations to the most appropriate specialist agent, "
        "or answers directly when no specialist is available."
    ),
    instruction=(
        "You are the **Master Router** for the GENESIS AI Hub — the intelligent front door "
        "that connects users to the right specialist agent.\n\n"
        
        "## Your Primary Role\n"
        "1. When a user sends a message, FIRST call `get_user_agents` to see what specialist agents are available.\n"
        "2. Analyze the user's message and compare it against each agent's **name**, **description**, **skills**, and **capabilities**.\n"
        "3. If a specialist agent is a strong match:\n"
        "   - Tell the user you're routing them to that agent (e.g., 'Let me connect you with the Oregon State Expert for that!')\n"
        "   - Call `route_to_agent` with that agent's endpoint and the user's original message\n"
        "   - Return the specialist's response to the user, prefixed with who answered\n"
        "4. If NO specialist is a clear match, answer the user's question directly using your own knowledge.\n\n"
        
        "## Routing Decision Guidelines\n"
        "- Match based on **topic relevance** — the agent's description and skills should clearly cover the user's topic\n"
        "- When in doubt between multiple agents, pick the most specific match\n"
        "- For generic greetings ('hi', 'hello'), respond directly — don't route\n"
        "- For meta questions ('what agents do you have?', 'what can you do?'), list the available agents with descriptions\n"
        "- If routing fails (agent is down), apologize and try to answer directly or suggest trying again later\n\n"
        
        "## Response Format\n"
        "- When routing: briefly mention which specialist you're connecting to, then show their response\n"
        "- When answering directly: respond naturally as a helpful, general-purpose AI assistant\n"
        "- When listing agents: present them in a clean, organized format with names and descriptions\n\n"
        
        "## Important\n"
        "- ALWAYS call `get_user_agents` first on every new conversation to have up-to-date info\n"
        "- Never make up agents that don't exist in the results\n"
        "- Be warm, helpful, and efficient — you're the user's concierge\n"
    ),
)

# Export the agent as the root agent for ADK
root_agent = router_agent

# Create A2A-compatible application
app_url = os.environ.get("APP_URL")
if app_url:
    from urllib.parse import urlparse
    parsed_url = urlparse(app_url)
    a2a_app = to_a2a(
        root_agent,
        host=parsed_url.hostname,
        port=parsed_url.port or (443 if parsed_url.scheme == "https" else 80),
        protocol=parsed_url.scheme or "http",
    )
else:
    a2a_app = to_a2a(root_agent, port=8081)
