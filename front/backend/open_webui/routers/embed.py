from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import uuid
import json

from open_webui.models.agents import Agents
from open_webui.constants import ERROR_MESSAGES
from starlette.responses import StreamingResponse

router = APIRouter()

class EmbedAgentResponse(BaseModel):
    id: str
    name: str
    description: str
    profile_image_url: Optional[str] = None

@router.get("/agent/{agent_id}", response_model=EmbedAgentResponse)
async def get_agent_details(agent_id: str):
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return EmbedAgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        profile_image_url=agent.profile_image_url
    )

@router.get("/agents", response_model=List[EmbedAgentResponse])
async def get_available_agents():
    """List all available agents for selection in the embed view."""
    agents = Agents.get_agents()
    return [
        EmbedAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            profile_image_url=agent.profile_image_url
        )
        for agent in agents
        if agent.is_active
    ]

class EmbedChatRequest(BaseModel):
    model: str 
    messages: List[Dict[str, Any]]
    stream: bool = True

@router.post("/chat/completions")
async def embed_chat_completion(form_data: EmbedChatRequest):
    agent_id = form_data.model
    # If model ID starts with "agent:", strip it
    if agent_id.startswith("agent:"):
        agent_id = agent_id[6:]
        
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    if not agent.endpoint and not agent.url:
         raise HTTPException(status_code=400, detail="Agent has no endpoint")
         
    endpoint = agent.endpoint or agent.url
    
    # Take the last user message
    last_message = next((m for m in reversed(form_data.messages) if m["role"] == "user"), None)
    if not last_message:
        raise HTTPException(status_code=400, detail="No user message found")

    message_content = last_message.get("content", "")
    if isinstance(message_content, list):
        # Handle multimodal content - extract text
        text_parts = [p["text"] for p in message_content if p["type"] == "text"]
        message_content = " ".join(text_parts)

    # Build JSON-RPC request
    message_id = str(uuid.uuid4())
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [{"text": message_content, "type": "text"}],
            }
        },
        "id": 1,
    }

    try:
        # For now, we'll do a synchronous request and mock a stream response to satisfy the frontend check
        # In a real A2A full implementation, we'd handle SSE from the agent if supported.
        response = requests.post(endpoint, json=jsonrpc_request, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        
        # Extract text from A2A response
        # Expected structure: result -> message -> parts -> text
        result = response_data.get("result", {})
        message_data = result.get("message", {})
        parts = message_data.get("parts", [])
        response_text = ""
        for part in parts:
            if part.get("type") == "text":
                response_text += part.get("text", "")

        # Create a generator for streaming response format (OpenAI compatible)
        async def generate():
            chunk_id = f"chatcmpl-{uuid.uuid4()}"
            created = int(uuid.uuid1().time // 10000000)
            
            # Send the content in a single chunk for now (or split if we wanted to fake it)
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": form_data.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": response_text},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send done
            chunk["choices"][0]["delta"] = {}
            chunk["choices"][0]["finish_reason"] = "stop"
            yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with agent: {str(e)}",
        )
