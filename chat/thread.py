from typing import List, Type
from .message import Message, ChatModel, ResponseFormat
from .provider import ProviderInterface


class ChatThread:
    provider: Type[ProviderInterface] = None
    model_type: ChatModel = None
    system_prompt: str = None
    messages: List[Message] = None
    temperature: float = None
    max_tokens: int = None

    def __init__(
        self,
        provider: Type[ProviderInterface],
        model_type: ChatModel,
        system_prompt: str,
        messages: List[Message],
        temperature: float = 0.4,
        max_tokens: int = 4000
    ):
        self.provider = provider
        self.model_type = model_type
        self.system_prompt = system_prompt
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens

    def add_message(self, message: Message):
        self.messages.append(message)

    def run(self, response_format: Type[ResponseFormat] = "text"):
        return self.provider.run(
            self.model_type,
            self.system_prompt,
            self.messages,
            self.max_tokens,
            self.temperature,
            response_format
        )
