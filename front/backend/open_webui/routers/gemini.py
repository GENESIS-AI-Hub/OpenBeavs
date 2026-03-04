import logging
import time

import openai
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("GEMINI", logging.INFO))

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

GEMINI_MODELS = [
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash-Lite"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
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
                "owned_by": "gemini",
            }
            for m in GEMINI_MODELS
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
    api_key = request.app.state.config.GEMINI_CHAT_API_KEY
    if not api_key:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)

    client = openai.AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)

    model_id = form_data.get("model", "gemini-2.0-flash")
    stream = form_data.get("stream", False)

    kwargs = {
        "model": model_id,
        "messages": form_data.get("messages", []),
    }
    if form_data.get("max_tokens") is not None:
        kwargs["max_tokens"] = form_data["max_tokens"]
    if form_data.get("temperature") is not None:
        kwargs["temperature"] = form_data["temperature"]
    if form_data.get("top_p") is not None:
        kwargs["top_p"] = form_data["top_p"]
    if form_data.get("stop"):
        kwargs["stop"] = form_data["stop"]

    if stream:

        async def event_generator():
            try:
                async with await client.chat.completions.create(
                    **kwargs, stream=True
                ) as stream_ctx:
                    async for chunk in stream_ctx:
                        yield f"data: {chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
            except openai.APIError as e:
                log.error(f"Gemini API error during streaming: {e}")
                import json
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
            response = await client.chat.completions.create(**kwargs)
            return response.model_dump()
        except openai.APIError as e:
            log.error(f"Gemini API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
