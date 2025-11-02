# Open WebUI 👋

**Open WebUI is an [extensible](https://docs.openwebui.com/features/plugin/), feature-rich, and user-friendly self-hosted AI platform designed to operate entirely offline.** It supports various LLM runners like **Ollama** and **OpenAI-compatible APIs**, with **built-in inference engine** for RAG, making it a **powerful AI deployment solution**.

![Open WebUI Demo](./demo.gif)

## Table of Contents
- [About This Fork](#about-this-fork)
- [Prerequisites](#prerequisites)
- [Part 1: Install Miniforge (Conda)](#part-1-install-miniforge-conda)
- [Part 2: Install NVM (Node Version Manager)](#part-2-install-nvm-node-version-manager)
- [Part 3: Clone the Repository](#part-3-clone-the-repository)
- [Part 4: Build and Run Open WebUI](#part-4-build-and-run-open-webui)
- [Development Workflow](#development-workflow)
- [A2A Protocol Integration](#a2a-protocol-integration)
- [Troubleshooting](#troubleshooting)
- [Debranding Guide](#debranding-guide)
- [Version Information](#version-information)
- [Legal and Attribution](#legal-and-attribution)
- [License](#license )

---

## About This Fork

This repository is a customized fork of [Open WebUI](https://github.com/open-webui/open-webui) based on **version 0.6.5** (commit: `07d8460126a686de9a99e2662d06106e22c3f6b6`).

### Repository Optimization

This fork has been minimized to reduce repository size and remove unnecessary artifacts:

**Size Reduction**: ~2.7GB → ~619MB (77% reduction)

#### What Was Removed:

- ✅ **Build Artifacts** (`node_modules/`, `build/`, `backend/static/`) - Regenerated during build process
- ✅ **Runtime Data** (`backend/data/cache/`, `backend/data/uploads/`, `backend/data/vector_db/`) - Created during runtime
- ✅ **Generated Assets** (`static/assets/`, `static/pyodide/`) - Rebuilt automatically
- ✅ **Original Project Documentation** (`CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `TROUBLESHOOTING.md`) - Replaced with custom docs

#### What's Preserved:

- ✅ **Source Code** - Complete v0.6.5 codebase
- ✅ **Configuration Files** - All necessary config files
- ✅ **Dependencies Manifests** - `package.json`, `requirements.txt`
- ✅ **Build Scripts** - All build and development scripts

### Why This Approach?

This lean repository approach:
- Reduces clone time and disk space usage
- Ensures users build with current dependencies
- Prevents committing generated or user-specific files
- Makes the repository easier to customize and maintain

All removed files are automatically regenerated when you follow the build instructions below.

### Customization Ready

This fork is prepared for customization and rebranding. See [Debranding Guide](#debranding-guide) section below for details.

---

## Prerequisites

Before you begin, ensure you have:

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Git**: Installed and configured

---

## Part 1: Install Miniforge (Conda)

Miniforge is a minimal installer for Conda that helps you manage Python environments and dependencies.

### On macOS/Linux:

```bash
# Download and install Miniforge
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# Follow the installation prompts:
# 1. Press ENTER to review the license
# 2. Type 'yes' to accept the license terms
# 3. Press ENTER to confirm the installation location (or specify custom path)
# 4. Type 'yes' when asked "Do you wish to update your shell profile to automatically initialize conda?"
```

### On Windows (WSL2):

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash Miniforge3-Linux-x86_64.sh
```

### Verify Installation:

```bash
# Close and reopen your terminal, or run:
source ~/.bashrc  # For bash users
# OR
source ~/.zshrc   # For zsh users

# Verify conda is installed
conda --version
# Expected output: conda 24.x.x or similar
```

---

## Part 2: Install NVM (Node Version Manager)

NVM allows you to install and manage multiple Node.js versions.

### Install NVM:

```bash
# Download and install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Close and reopen your terminal, or run:
source ~/.bashrc  # For bash users
# OR
source ~/.zshrc   # For zsh users

# Verify NVM is installed
nvm --version
# Expected output: 0.39.0 or similar
```

### Install Node.js 22:

```bash
# Install Node.js version 22 (required by Open WebUI)
nvm install 22

# Set Node.js 22 as the active version
nvm use 22

# Set Node.js 22 as the default version
nvm alias default 22

# Verify Node.js installation
node --version
# Expected output: v22.x.x

npm --version
# Expected output: 10.x.x or similar
```

---

## Part 3: Clone the Forked Repository

### Fork and Clone:

1. Go to Open WebUI forked copy on GitHub: `https://github.com/minkim26/open-webui`
2. Copy the clone URL

```bash
# Clone the forked repository
git clone https://github.com/minkim26/open-webui.git

# Navigate into the repository
cd open-webui

# Verify you're on the main branch
git branch --show-current
# Expected output: main

# If not on the main branch, switch to it:
git checkout main
```

---

## Part 4: Build and Run Open WebUI

### Step 1: Set Up Python Environment

```bash
# Navigate to the backend directory
cd backend

# Create a new Conda environment with Python 3.11
conda create --name open-webui python=3.11

# When prompted "Proceed ([y]/n)?", type: y

# Activate the environment
conda activate open-webui

# Your terminal prompt should now show: (open-webui)

# Install Python dependencies
pip install -r requirements.txt -U

# This will take several minutes...
```

### Step 2: Build the Frontend

```bash
# Navigate back to the project root
cd ..

# Ensure you're using Node.js 22
nvm use 22

# Copy the environment file
cp -RPp .env.example .env

# Install frontend dependencies
npm install

# If you encounter errors, try:
npm install --force

# Build the frontend (this compiles it into static files)
npm run build
```

This creates an optimized production build in the `build/` directory.

### Step 3: Copy Built Frontend to Backend

```bash
# Copy the built frontend to the backend's static directory
cp -r build backend/static

# Verify the files were copied
ls -la backend/static/
```

### Step 4: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Make sure your conda environment is activated
conda activate open-webui

# Start the backend development server
sh dev.sh
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Access Open WebUI

Open your web browser and navigate to:

**http://localhost:8080**

You should see the Open WebUI interface! 🎉

**API Documentation is available at:**

**http://localhost:8080/docs**

---

## Development Workflow

### Starting Open WebUI:

```bash
# Terminal 1: Navigate to backend and start server
cd ~/open-webui/backend
conda activate open-webui
sh dev.sh

# Access at: http://localhost:8080
```

### Making Frontend Changes:

When you modify frontend code, you need to rebuild:

```bash
# Terminal 2: Navigate to project root
cd ~/open-webui

# Ensure you're using Node 22
nvm use 22

# Rebuild the frontend
npm run build

# Copy the new build to backend
cp -r build backend/static

# The backend will automatically detect changes if dev.sh is running
```

### Stopping the Server:

In the terminal running the backend, press `Ctrl+C`

---

## A2A Protocol Integration

This Open WebUI fork now includes full **Agent-to-Agent (A2A) Protocol** support, allowing it to discover, register, and communicate with external AI agents using JSON-RPC 2.0.

### What is A2A Protocol?

The A2A protocol enables AI agents to:
- **Discover** each other through `.well-known/agent.json` endpoints
- **Communicate** using standardized JSON-RPC 2.0 messaging
- **Register** with hub services for coordination
- **Exchange** structured messages with defined schemas

### Architecture Overview

```
┌─────────────────────────────────────┐
│   Open WebUI (Port 8080)            │
│   - A2A Hub & Agent                 │
│   - Manages registered agents       │
│   - Routes messages                 │
└──────────────┬──────────────────────┘
               │ A2A Protocol
               │ (JSON-RPC 2.0)
               │
┌──────────────┴──────────────────────┐
│   GENESIS AI Hub (Port 8000)        │
│   - A2A Backend Server              │
│   - Agent Registry                  │
│   - Chat Management                 │
└─────────────────────────────────────┘
```

### A2A Features Implemented

✅ **Agent Discovery**: `.well-known/agent.json` endpoint
✅ **Agent Registry**: Full CRUD operations for agents
✅ **JSON-RPC 2.0**: Standard messaging protocol
✅ **REST API**: `/api/v1/agents` endpoints for management
✅ **Database Persistence**: Agents stored in SQLite
✅ **Agent Communication**: Send messages to registered agents

---

### Setup: Running Both Services

To test the A2A protocol integration, you need to run both Open WebUI and the GENESIS AI Hub backend.

#### Terminal 1: Start Open WebUI (A2A Hub)

```bash
# Navigate to open-webui backend
cd /Users/minsoup/GENESIS-AI-Hub-App/open-webui/backend

# Activate conda environment
conda activate open-webui

# Start the server
sh dev.sh

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8080
```

**Open WebUI will be available at:**
- Web Interface: http://localhost:8080
- API Docs: http://localhost:8080/docs
- A2A Discovery: http://localhost:8080/.well-known/agent.json

#### Terminal 2: Start GENESIS AI Hub Backend (A2A Server)

```bash
# Navigate to the main backend directory
cd /Users/minsoup/GENESIS-AI-Hub-App/back

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --port 8000

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

**GENESIS AI Hub will be available at:**
- API Root: http://localhost:8000
- A2A Discovery: http://localhost:8000/.well-known/agent.json
- API Docs: http://localhost:8000/docs

---

### Testing A2A Protocol

#### Step 1: Verify A2A Discovery Endpoints

Test that both services expose their A2A discovery information:

```bash
# Test Open WebUI A2A discovery
curl http://localhost:8080/.well-known/agent.json | jq

# Expected output: Agent information with capabilities, skills, etc.
```

```bash
# Test GENESIS AI Hub A2A discovery
curl http://localhost:8000/.well-known/agent.json | jq

# Expected output: Hub agent information
```

#### Step 2: Register GENESIS AI Hub as an Agent

Register the GENESIS AI Hub backend with Open WebUI:

```bash
# Register by URL (automatic discovery)
curl -X POST http://localhost:8080/api/v1/agents/register-by-url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "agent_url": "http://localhost:8000"
  }' | jq

# Expected output: Registered agent details with ID
```

**Note**: You'll need to be authenticated. Get a token by:
1. Opening http://localhost:8080 in your browser
2. Creating an account or logging in
3. Going to Settings → Account → API Key
4. Copying your API key to use as the Bearer token

#### Step 3: List Registered Agents

```bash
# List all active agents
curl http://localhost:8080/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" | jq

# You should see the registered GENESIS AI Hub agent
```

#### Step 4: Send a Message to a Registered Agent

```bash
# Replace {agent_id} with the ID from step 2
curl -X POST http://localhost:8080/api/v1/agents/{agent_id}/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "message": "Hello from Open WebUI! Testing A2A communication."
  }' | jq

# Expected output: Response from the agent
```

#### Step 5: Test JSON-RPC Endpoint

Test the JSON-RPC endpoint directly:

```bash
# Send a JSON-RPC message
curl -X POST http://localhost:8080/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-123",
        "role": "user",
        "parts": [
          {
            "text": "Hello A2A!",
            "type": "text"
          }
        ]
      }
    },
    "id": 1
  }' | jq

# Expected output: JSON-RPC response with result
```

---

### A2A API Endpoints Reference

#### Agent Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents` | List all active agents |
| GET | `/api/v1/agents/{agent_id}` | Get specific agent details |
| POST | `/api/v1/agents/register` | Manually register an agent |
| POST | `/api/v1/agents/register-by-url` | Register agent from `.well-known/agent.json` |
| GET | `/api/v1/agents/fetch-well-known?agent_url=...` | Preview agent info without registering |
| PATCH | `/api/v1/agents/{agent_id}` | Update agent details |
| DELETE | `/api/v1/agents/{agent_id}` | Delete/unregister an agent |
| POST | `/api/v1/agents/{agent_id}/message` | Send message to agent via A2A |

#### A2A Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/.well-known/agent.json` | Agent discovery (returns Open WebUI capabilities) |
| POST | `/jsonrpc` | JSON-RPC 2.0 message endpoint |

---

### Example: Complete A2A Workflow

Here's a complete example of the A2A workflow:

```bash
# 1. Verify both services are running
curl http://localhost:8080/health
curl http://localhost:8000/

# 2. Discover the external agent
curl http://localhost:8000/.well-known/agent.json | jq

# 3. Register the agent with Open WebUI
AGENT_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/agents/register-by-url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"agent_url": "http://localhost:8000"}')

echo $AGENT_RESPONSE | jq

# 4. Extract the agent ID
AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')
echo "Registered Agent ID: $AGENT_ID"

# 5. Send a test message to the agent
curl -X POST "http://localhost:8080/api/v1/agents/$AGENT_ID/message" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "message": "Hello! Can you help me with a task?"
  }' | jq

# 6. List all registered agents
curl http://localhost:8080/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" | jq
```

---

### Integration with GENESIS AI Hub Backend

The GENESIS AI Hub backend (`/back/main.py`) provides:

- **Agent Registry**: Stores and manages available agents
- **Chat Management**: Maintains conversation history
- **Message Routing**: Routes messages to appropriate agents
- **JSON-RPC Server**: Implements A2A protocol server

#### GENESIS AI Hub Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/.well-known/agent.json` | A2A discovery endpoint |
| POST | `/jsonrpc` | JSON-RPC 2.0 message handler |
| GET | `/agents` | List registered agents in hub |
| POST | `/agents/register` | Register a new agent |
| POST | `/agents/register-by-url` | Register agent by URL |
| GET | `/chats` | List all chat threads |
| POST | `/chats` | Create a new chat thread |
| GET | `/chats/{chat_id}/messages` | Get messages in a chat |
| POST | `/chats/{chat_id}/messages` | Send message in a chat |

---

### Database Schema

The A2A integration adds an `agent` table to Open WebUI's database:

```sql
CREATE TABLE agent (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    endpoint TEXT,
    url TEXT,
    version TEXT,
    capabilities JSON,
    skills JSON,
    default_input_modes JSON,
    default_output_modes JSON,
    input_schema JSON,
    output_schema JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    user_id TEXT
);
```

The migration runs automatically when you start Open WebUI for the first time after integration.

---

### Development Tips

#### Viewing Logs

**Open WebUI logs:**
```bash
# The logs appear in the terminal where you ran `sh dev.sh`
# Look for A2A-related messages during agent registration
```

**GENESIS AI Hub logs:**
```bash
# Logs appear in the terminal where you ran `uvicorn`
# Shows incoming JSON-RPC requests and responses
```

#### Debugging Agent Communication

1. **Check agent is registered:**
   ```bash
   curl http://localhost:8080/api/v1/agents \
     -H "Authorization: Bearer YOUR_TOKEN" | jq
   ```

2. **Verify endpoint is accessible:**
   ```bash
   curl http://localhost:8000/.well-known/agent.json
   ```

3. **Test direct JSON-RPC call:**
   ```bash
   curl -X POST http://localhost:8000/jsonrpc \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "message/send",
       "params": {
         "message": {
           "messageId": "test-123",
           "role": "user",
           "parts": [{"text": "test", "type": "text"}]
         }
       },
       "id": 1
     }' | jq
   ```

#### Database Inspection

View registered agents in the database:

```bash
# Navigate to the backend data directory
cd /Users/minsoup/GENESIS-AI-Hub-App/open-webui/backend/open_webui/data

# Open the database with sqlite3
sqlite3 webui.db

# Query agents
sqlite> SELECT id, name, endpoint, is_active FROM agent;
sqlite> .quit
```

---

### Next Steps

Now that you have A2A protocol working, you can:

1. **Build Custom Agents**: Create your own A2A-compatible agents
2. **Connect Multiple Agents**: Register multiple agents and route messages between them
3. **Extend the Protocol**: Add custom capabilities and skills
4. **Integrate with Frontend**: Build UI components to manage agents visually
5. **Deploy to Production**: Use Docker and cloud services for deployment

For more information about the A2A protocol and best practices, refer to the [GENESIS AI Hub documentation](../README.md).

---

## Troubleshooting

### "conda: command not found"

```bash
# Reinitialize your shell
source ~/.bashrc  # For bash
# OR
source ~/.zshrc   # For zsh

# If still not working, manually add to your profile:
echo 'export PATH="$HOME/miniforge3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "nvm: command not found"

```bash
# Add NVM to your shell profile manually
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc
source ~/.bashrc
```

### "Open WebUI Backend Required" Error

This means the frontend isn't being served from the backend. Solution:

```bash
# Rebuild and copy frontend
cd ~/open-webui
npm run build
cp -r build backend/static

# Restart backend
cd backend
conda activate open-webui
sh dev.sh

# Access at http://localhost:8080 (NOT 5173)
```

### Backend Won't Start

```bash
# Check if port 8080 is already in use
lsof -i :8080

# If something is using it, kill that process:
kill -9 <PID>

# Try starting the backend again
```

### Python Dependencies Installation Fails

```bash
# Recreate the conda environment
conda deactivate
conda remove --name open-webui --all
conda create --name open-webui python=3.11
conda activate open-webui
pip install -r requirements.txt -U
```

### Frontend Build Fails

```bash
# Clear npm cache and node_modules
rm -rf node_modules package-lock.json
npm cache clean --force

# Reinstall dependencies
npm install --force

# Try building again
npm run build
```

### Browser Shows Blank Page

```bash
# Check if static files exist
ls -la backend/static/

# If empty, rebuild and copy:
cd ~/open-webui
npm run build
cp -r build backend/static

# Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
```

---

## Debranding Guide

For future plans to rebrand this fork, modify the following:

1. **README.md** - Update all "Open WebUI" references
2. **package.json** - Change `"name": "open-webui"` to your project name
3. **backend/open_webui/env.py** - Update:
   ```python
   WEBUI_NAME = "Your Project Name"
   WEBUI_FAVICON_URL = "your-favicon-url"
   ```
4. **backend/open_webui/main.py** - Update repository references
5. **Translation files** (`src/lib/i18n/locales/`) - Contains "Open WebUI" text
6. **Configuration files** - Service names and references
7. **Docker files** - Customize for your branding
8. **INSTALLATION.md** - Update installation instructions

### Recommended Approach:

```bash
# Search for all "Open WebUI" references
grep -r "Open WebUI" . --exclude-dir={node_modules,build,backend/static}

# Search for "open-webui" references
grep -r "open-webui" . --exclude-dir={node_modules,build,backend/static}

# Update incrementally and test after each major change
```

---

## Version Information

- **Open WebUI Version**: v0.6.5
- **Commit SHA**: `07d8460126a686de9a99e2662d06106e22c3f6b6`
- **Python Version**: 3.11+
- **Node.js Version**: 22+

---

## Legal and Attribution

This repository is a customized fork of the original [Open WebUI](https://github.com/open-webui/open-webui) project © 2023–2025 Timothy Jaeryang Baek, originally released under the **BSD 3-Clause License**.

This fork includes modifications and rebranding by © 2025 Oregon State University, and all new contributions are licensed under the **MIT License**.

---

## License

This project is licensed under the [MIT License](./LICENSE).
Portions of this work retain the original Open WebUI BSD 3-Clause License terms.

- Portions of this project are derived from the Open WebUI source code and remain covered by the original BSD 3-Clause License.
- Modifications, additions, and new files authored by Oregon State University are provided under the MIT License.
- The full license terms are available in the [LICENSE](./LICENSE) file.
- Neither the name “Open WebUI” nor the names of its original contributors may be used to endorse or promote derivative products.

By using this codebase, you agree to comply with the licensing conditions specified in both the upstream Open WebUI BSD 3-Clause License and the MIT License governing this fork.
