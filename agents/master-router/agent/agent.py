
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import os
import httpx
import threading
import time
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Configuration
OPENWEBUI_URL = os.environ.get("OPENWEBUI_URL", "http://localhost:8080")
OPENWEBUI_API_KEY = os.environ.get("OPENWEBUI_API_KEY", "")
DISCOVERY_RETRY_INTERVAL = int(os.environ.get("DISCOVERY_RETRY_INTERVAL", "5"))
DISCOVERY_MAX_RETRIES = int(os.environ.get("DISCOVERY_MAX_RETRIES", "24"))


# ─── Discover agents from Open WebUI ─────────────────────────────────

def _fetch_agents_from_api() -> list:
    """Fetch the list of registered agents from the Open WebUI API."""
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
    return response.json()


def _build_sub_agents(agents_data: list) -> list[RemoteA2aAgent]:
    """Create RemoteA2aAgent instances from the agents data."""
    sub_agents = []
    seen_endpoints = set()

    for agent_data in agents_data:
        name = agent_data.get("name", "")
        endpoint = agent_data.get("endpoint", "")

        # Skip the Master Router itself and agents without endpoints
        if name.lower() == "master router" or not endpoint:
            continue

        # Skip duplicate endpoints (same agent registered twice)
        if endpoint in seen_endpoints:
            continue
        seen_endpoints.add(endpoint)

        # Normalize the endpoint URL for the agent card
        base_url = endpoint.rstrip("/")
        if base_url.startswith("https://") and base_url.endswith(":443"):
            base_url = base_url[:-4]

        # Create a clean agent name (must be valid Python identifier for ADK)
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower()).strip('_')
        if not clean_name:
            clean_name = f"agent_{agent_data.get('id', 'unknown')}"

        description = agent_data.get("description", f"Remote agent: {name}")

        try:
            remote_agent = RemoteA2aAgent(
                name=clean_name,
                agent_card=base_url,
                description=description,
            )
            sub_agents.append(remote_agent)
            print(f"[Router] Registered sub-agent: {clean_name} -> {base_url}")
        except Exception as e:
            print(f"[Router] Failed to create sub-agent '{name}': {type(e).__name__}: {e}")

    return sub_agents


def _discover_with_retry() -> list[RemoteA2aAgent]:
    """Discover specialist agents, retrying until Open WebUI is available."""
    for attempt in range(1, DISCOVERY_MAX_RETRIES + 1):
        try:
            agents_data = _fetch_agents_from_api()
            print(f"[Router] Discovered {len(agents_data)} agents from Open WebUI")
            return _build_sub_agents(agents_data)
        except Exception as e:
            print(f"[Router] Discovery attempt {attempt}/{DISCOVERY_MAX_RETRIES} failed: {type(e).__name__}: {e}")
            if attempt < DISCOVERY_MAX_RETRIES:
                print(f"[Router] Retrying in {DISCOVERY_RETRY_INTERVAL}s...")
                time.sleep(DISCOVERY_RETRY_INTERVAL)
    
    print("[Router] WARNING: All discovery attempts failed. Starting with 0 sub-agents.")
    return []


# ─── Build the agent tree ────────────────────────────────────────────

print("[Router] Discovering specialist agents...")
discovered_sub_agents = _discover_with_retry()
print(f"[Router] {len(discovered_sub_agents)} sub-agents ready")

router_agent = Agent(
    name="master_router",
    model=os.environ.get("ROUTER_MODEL", "gemini-2.5-flash"),
    sub_agents=discovered_sub_agents,
    description=(
        "The Master Router Agent for GENESIS AI Hub. "
        "Intelligently routes user conversations to the most appropriate specialist agent, "
        "or answers directly when no specialist is available."
    ),
    instruction=(
        "You are the **Master Router** for the GENESIS AI Hub — the intelligent front door "
        "that connects users to the right specialist agent.\n\n"

        "## Your Primary Role\n"
        "Analyze the user's message and delegate to the most appropriate specialist sub-agent.\n"
        "If no specialist is a clear match, answer the user's question directly using your own knowledge.\n\n"

        "## Routing Decision Guidelines\n"
        "- Match based on **topic relevance** — the sub-agent's description should clearly cover the user's topic\n"
        "- When in doubt between multiple agents, pick the most specific match\n"
        "- For generic greetings ('hi', 'hello'), respond directly — don't delegate\n"
        "- For meta questions ('what agents do you have?', 'what can you do?'), respond directly with the list of available sub-agents and their descriptions — do NOT delegate these\n\n"

        "## Important\n"
        "- Be warm, helpful, and efficient — you're the user's concierge\n"
        "- When delegating, let the sub-agent handle the response fully\n"
        "- Never make up agents that don't exist as your sub-agents\n"
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
