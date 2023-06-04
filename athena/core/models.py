import logging

from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class LoggerConfig(BaseModel):
    handlers: list
    format: str | None
    date_format: str | None = None
    logger_file: Path | None = None
    level: int = logging.DEBUG


class Overrides(BaseModel):
    semantic_ranker: bool = False
    semantic_captions: bool = False
    exclude_category: str | None = None
    top: int | None = 3
    temperature: float = 0.7
    suggest_followup_questions: bool = True


class ChatHistory(BaseModel):
    user: str
    bot: str | None = None


class Chat(BaseModel):
    approach: Literal["rrr"]
    history: list[ChatHistory]
    overrides: Overrides | None = None


class MessagePrompt(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str | None
    name: str = ""


class MessageResponse(BaseModel):
    data_points: list[str]
    answer: str
    thoughts: str
