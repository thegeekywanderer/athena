import openai
import mimetypes
import enum

from fastapi import APIRouter, Request, Response, HTTPException
from athena.libs.chat.readretrieveread import ReadRetrieveReadApproach
from athena.core.config import OpenAISettings
from athena.core.models import Chat, MessageResponse

router = APIRouter(tags=["chat"], prefix="/chat")

chat_approaches = {"rrr": ReadRetrieveReadApproach("sourcepage", "content")}
openai_config = OpenAISettings()
openai.api_key = openai_config.api_key


@router.post("/")
async def chat(request: Request, chat: Chat) -> MessageResponse:
    search_client = request.app.state.cognitive_search
    try:
        impl = chat_approaches.get(chat.approach)
        if not impl:
            return HTTPException(status_code=400, detail="unknown approach")
        chat_response = impl.run(
            search_client=search_client,
            history=chat.history,
            overrides=chat.overrides,
        )
        return chat_response
    except Exception as e:
        raise e


@router.get("/content/{path}")
async def content(request: Request, path: str, response: Response):
    blob_container = request.app.state.blob_container
    blob = blob_container.get_blob_client(path).download_blob()
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    response.headers["Content-Type"] = mime_type
    response.headers["Content-Disposition"] = f"inline; filename={path}"
    return (blob.readall(),)
