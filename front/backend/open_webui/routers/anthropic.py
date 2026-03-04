import json
import logging
import time
import uuid

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("ANTHROPIC", logging.INFO))

CLAUDE_MODELS = [
    {"id": "claude-opus-4-6", "name": "Claude Opus 4.6"},
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6"},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
]

router = APIRouter()


async def get_all_models(request: Request, user: UserModel = None):
    return {
        "object": "list",
        "data": [
            {
                "id": m["id"],
                "name": m["name"],
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            }
            for m in CLAUDE_MODELS
        ],
    }


@router.get("/models")
async def list_models(request: Request, user=Depends(get_verified_user)):
    return await get_all_models(request, user=user)


async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user: UserModel,
    bypass_filter: bool = False,
):
    api_key = request.app.state.config.ANTHROPIC_API_KEY
    if not api_key:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)

    messages = form_data.get("messages", [])
    system_parts = []
    anthropic_messages = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        system_parts.append(part["text"])
                    elif isinstance(part, str):
                        system_parts.append(part)
            else:
                system_parts.append(str(content))
        elif role in ("user", "assistant"):
            anthropic_messages.append({"role": role, "content": content})

    # Anthropic requires the first message to be from "user"
    if anthropic_messages and anthropic_messages[0]["role"] != "user":
        anthropic_messages.insert(0, {"role": "user", "content": ""})

    model_id = form_data.get("model", "claude-sonnet-4-6")
    max_tokens = form_data.get("max_tokens") or 8192
    stream = form_data.get("stream", False)

    kwargs = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": anthropic_messages,
    }
    if system_parts:
        kwargs["system"] = "\n\n".join(system_parts)
    if form_data.get("temperature") is not None:
        kwargs["temperature"] = form_data["temperature"]
    if form_data.get("top_p") is not None:
        kwargs["top_p"] = form_data["top_p"]
    if form_data.get("stop"):
        kwargs["stop_sequences"] = (
            form_data["stop"]
            if isinstance(form_data["stop"], list)
            else [form_data["stop"]]
        )

    async_client = anthropic.AsyncAnthropic(api_key=api_key)
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    if stream:

        async def event_generator():
            try:
                async with async_client.messages.stream(**kwargs) as stream_ctx:
                    async for text in stream_ctx.text_stream:
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": text},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    # Send final chunk with finish_reason
                    final_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model_id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
            except anthropic.APIError as e:
                log.error(f"Anthropic API error during streaming: {e}")
                error_payload = {"error": {"message": str(e), "type": "api_error"}}
                yield f"data: {json.dumps(error_payload)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        try:
            response = await async_client.messages.create(**kwargs)
            content = response.content[0].text if response.content else ""
            return {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": response.stop_reason or "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
            }
        except anthropic.APIError as e:
            log.error(f"Anthropic API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
