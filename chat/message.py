from enum import Enum
from typing import Literal


class ChatModel(Enum):
    ADVANCED = "chat_advanced"
    SUPER = "chat_super"
    MM_ADVANCED = "multimodal_advanced"
    MM_SUPER = "multimodal_super"


class ResponseFormat(Enum):
    JSON = "json"
    TEXT = "text"
    PYTHON = "python"
    FUNCTION_CALLS = "function_calls"


class Message:
    content: str = None
    role: Literal['user', 'assistant'] = None
    type: Literal['text', 'image'] = None

    def __init__(self, content: str, role: Literal['user', 'assistant'], type: Literal['text', 'image']):
        self.content = content
        self.role = role
        self.type = type

    def __str__(self):
        return f"msg(content={self.content}, role={self.role}, type={self.type})"