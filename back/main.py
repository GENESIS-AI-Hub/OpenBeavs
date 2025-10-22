from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import asyncio
import json

app = FastAPI()

# Allow all origins for simplicity, but you should restrict this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demonstration (would use database in production)
chats_db: Dict[str, dict] = {}
messages_db: Dict[str, List[dict]] = {}
agents_db: List[dict] = []

# Data models
class Chat(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    agent_id: str

class Message(BaseModel):
    id: str
    chat_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    files: Optional[List[dict]] = None

class Agent(BaseModel):
    id: str
    name: str
    description: str
    endpoint: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None

class CreateChatRequest(BaseModel):
    title: str
    agent_id: str

class SendMessageRequest(BaseModel):
    content: str
    files: Optional[List[dict]] = None

class RegisterAgentRequest(BaseModel):
    name: str
    description: str
    endpoint: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None

# Initialize with example agent
@app.on_event("startup")
def startup_event():
    # Register example agent
    example_agent = Agent(
        id="cyrano_agent",
        name="Cyrano de Bergerac",
        description="A poetic assistant that responds with eloquent, flowery language",
        endpoint=None,
        input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"response": {"type": "string"}}}
    )
    agents_db.append(example_agent.dict())

# Chat endpoints
@app.get("/")
def read_root():
    return {"message": "OSU Genesis Hub Backend - Ready!"}

@app.get("/chats", response_model=List[Chat])
def get_chats():
    """Get all chat threads"""
    return [Chat(**chat_data) for chat_data in chats_db.values()]

@app.post("/chats", response_model=Chat)
def create_chat(chat_request: CreateChatRequest):
    """Create a new chat thread"""
    chat_id = str(uuid.uuid4())
    
    # Verify agent exists
    agent_exists = any(agent["id"] == chat_request.agent_id for agent in agents_db)
    if not agent_exists:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    chat = Chat(
        id=chat_id,
        title=chat_request.title,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        agent_id=chat_request.agent_id
    )
    
    chats_db[chat_id] = chat.dict()
    messages_db[chat_id] = []
    
    return chat

@app.get("/chats/{chat_id}", response_model=Chat)
def get_chat(chat_id: str):
    """Get a specific chat thread"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return Chat(**chats_db[chat_id])

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str):
    """Delete a chat thread"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    del chats_db[chat_id]
    if chat_id in messages_db:
        del messages_db[chat_id]
    
    return {"message": "Chat deleted successfully"}

# Message endpoints
@app.get("/chats/{chat_id}/messages", response_model=List[Message])
def get_messages(chat_id: str):
    """Get all messages in a chat thread"""
    if chat_id not in messages_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return [Message(**msg) for msg in messages_db[chat_id]]

@app.post("/chats/{chat_id}/messages", response_model=Message)
def send_message(chat_id: str, message_request: SendMessageRequest):
    """Send a message to a chat and get a response"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # Add user message
    user_message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role="user",
        content=message_request.content,
        timestamp=datetime.now(),
        files=message_request.files
    )
    
    messages_db[chat_id].append(user_message.dict())
    
    # Get the agent for this chat
    chat_agent_id = chats_db[chat_id]["agent_id"]
    agent = next((a for a in agents_db if a["id"] == chat_agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Generate response from agent
    response_content = generate_agent_response(message_request.content, agent)
    
    # Add assistant message
    assistant_message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role="assistant",
        content=response_content,
        timestamp=datetime.now()
    )
    
    messages_db[chat_id].append(assistant_message.dict())
    
    # Update chat timestamp
    chats_db[chat_id]["updated_at"] = datetime.now()
    
    return assistant_message

# Agent endpoints
@app.get("/agents", response_model=List[Agent])
def get_agents():
    """Get all registered agents"""
    return [Agent(**agent_data) for agent_data in agents_db]

@app.post("/agents/register", response_model=Agent)
def register_agent(agent_request: RegisterAgentRequest):
    """Register a new agent"""
    agent_id = str(uuid.uuid4())
    
    agent = Agent(
        id=agent_id,
        name=agent_request.name,
        description=agent_request.description,
        endpoint=agent_request.endpoint,
        input_schema=agent_request.input_schema,
        output_schema=agent_request.output_schema
    )
    
    agents_db.append(agent.dict())
    return agent

def generate_agent_response(user_message: str, agent: dict) -> str:
    """Generate response from an agent based on user message"""
    if agent["id"] == "cyrano_agent":
        # Cyrano de Bergerac agent responds in an eloquent, poetic way
        response_templates = [
            f"Ah, dear interlocutor, what you speak of '{user_message}' doth stir within me thoughts most profound...",
            f"'{user_message}', you say? How wondrous that fate hath brought us to discourse upon such matters...",
            f"With quill in hand and thoughts aflutter, I ponder your words '{user_message}' with the reverence they deserve...",
            f"Verily, your inquiry regarding '{user_message}' doth remind me of the beauty that lies in thoughtful contemplation...",
            f"In the symphony of discourse, your words '{user_message}' play a melody both sweet and intriguing..."
        ]
        import random
        return random.choice(response_templates)
    else:
        # Default response for other agents
        return f"I'm {agent['name']}. You said: '{user_message}'. How may I assist you?"
