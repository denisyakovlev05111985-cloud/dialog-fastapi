from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.config import settings
from app.database import Chat, Message, get_db, utc_now
from app.polza import PolzaError, polza

router = APIRouter(prefix="/api", tags=["chats"])
DbSession = Annotated[Session, Depends(get_db)]

class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    role: Literal["user", "assistant"]
    content: str
    model_id: str | None
    created_at: datetime

class ChatDetail(BaseModel):
    chat: ChatResponse
    messages: list[MessageResponse]

class CreateChatRequest(BaseModel):
    title: str = Field(default="Новый чат", min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def normalize_name(cls, value: str) -> str:
            value = " ".join(value.split())
            if len(value) < 2:
                raise ValueError("Название чата не может быть пустым")
            return value

class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    model_id: str = Field(min_length=1, max_length=255)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Сообщение не может быть пустым")

        return value

class SendMessageResponse(BaseModel):
    chat: ChatResponse
    assistant_message: MessageResponse

class ModelResponse(BaseModel):
    id: str
    name: str

def required_chat(chat_id: int, user_id: int, db: Session) -> Chat:
    chat = db.scalar(select(Chat.id == chat_id, Chat.user_id == user_id))

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден"
        )
    return chat

@router.get("/models", response_model=list[ModelResponse])
async def list_models() -> list[dict[str, str]]:
    try:
        return await polza.list_models()
    except PolzaError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)

        )
@router.get("/chats", response_model=list[ChatResponse])
async def list_chats(user: CurrentUser, db: DbSession):
    return list(
        db.scalar(
            select (Chat)
                .where(Chat.user_id == user.id)
                .order_by(Chat.updated_at.desc())))

@router.post(
    "/chats",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED
)

def create_chat(
    payload: CreateChatRequest,
    user: CurrentUser,
    db: DbSession
) -> Chat:
    chat = Chat(user_id=user.id, title=payload.title)
    db.add(chat)
    db.commit()
    return chat


@router.get("/chats/{chat_id}", response_model=ChatDetail)
def get_chat(chat_id: int, user: CurrentUser, db: DbSession) -> ChatDetail:
    chat = required_chat(chat_id, user.id, db)
    messages = list(
        db.scalar(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(Message.created_at)
        )
    )
    return ChatDetail(chat=chat, messages=messages)

@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, user: CurrentUser, db: DbSession):
    chat = required_chat(chat_id, user.id, db)
    db.delete(chat)
    db.commit()

@router.post("/chats/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_id: int,
    payload: SendMessageRequest,
    user: CurrentUser,
    db: DbSession
) -> SendMessageResponse:
    chat = required_chat(chat_id, user.id, db)
    recent = list(
        db.scalar(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(Message.created_at)
            .limit(settings.max_chat_history_messages)
        )
    )

    history = [
        { "role": message.role, "content": message.content }
        for message in reversed(recent)
    ]

    history.append({"role": "user", "content": payload.content})

    try:
        reply = await polza.complete(payload.model_id, history)
    except PolzaError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        ) from exc

    user_message = Message(
        chat_id=chat.id,
        role="user",
        content=payload.content,
        model_id=payload.model_id
    ) 

    assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=reply,
            model_id=payload.model_id
        ) 

    if chat.title == "Новый чат":
        chat.title = payload.content[:60] + ("..." if len(payload.content) > 60 else "")

    chat.updated_at = utc_now()
    db.add_all((user_message, assistant_message))
    db.commit()

    return SendMessageResponse(chat=chat, assistant_message=assistant_message)





            
    
                      