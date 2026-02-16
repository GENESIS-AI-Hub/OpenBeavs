# Master Router Agent

The Master Router Agent is the intelligent front door of the GENESIS AI Hub. It automatically routes user conversations to the most appropriate specialist agent based on context, or answers directly when no specialist is available.

## How It Works

1. **User sends a message** → Router Agent receives it
2. **Router fetches installed agents** → Calls Open WebUI API to discover available specialist agents
3. **Router analyzes the message** → Compares against each agent's name, description, skills, and capabilities
4. **Routes or answers directly**:
   - If a specialist matches → forwards the message via A2A protocol and returns the specialist's response
   - If no match → answers directly as a general-purpose assistant

## Setup

### Prerequisites
- Python 3.11+
- A Google API key (Gemini)
- Open WebUI running with A2A agents installed

### Local Development

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Edit .env with your keys
#    - GEMINI_API_KEY: Your Google Gemini API key
#    - OPENWEBUI_URL: URL of your Open WebUI instance (default: http://localhost:8080)
#    - OPENWEBUI_API_KEY: Your Open WebUI API key (Settings → Account → API Key)

# 3. Install dependencies
pip install -r requirements.txt
pip install -r agent/requirements.txt

# 4. Run the agent
python -m agent.agent
# or
adk run agent
```

The agent will start on port **8081** by default.

### Docker

```bash
docker build -t master-router .
docker run -p 8081:8081 --env-file .env master-router
```

## Registering with Open WebUI

After starting the agent, register it with Open WebUI:

1. Go to **Workspace → Agents** in the UI
2. Click **+** and enter `http://localhost:8081`
3. Or use the API:
   ```bash
   curl -X POST http://localhost:8080/api/v1/agents/register-by-url \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"agent_url": "http://localhost:8081"}'
   ```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | (required) | Google Gemini API key |
| `ROUTER_MODEL` | `gemini-2.5-flash` | Model to use for routing decisions |
| `OPENWEBUI_URL` | `http://localhost:8080` | Open WebUI backend URL |
| `OPENWEBUI_API_KEY` | (required) | API key for fetching user agents |
| `APP_URL` | (optional) | Override for Cloud Run deployment URL |
