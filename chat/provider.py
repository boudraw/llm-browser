from abc import ABC, abstractmethod
from typing import List
from chat.message import ChatModel, ResponseFormat, Message
from chat.tool import Tool
from memory.embeddings import EmbeddingModel


class ProviderInterface(ABC):
    @abstractmethod
    def get_chat_model(
        self,
        model_type: ChatModel
    ):
        pass

    @abstractmethod
    def get_vector_model(
        self,
        model_type: EmbeddingModel
    ):
        pass

    @abstractmethod
    def vectorize(
        self,
        text: str,
        dimensions: int,
        model_type: EmbeddingModel
    ):
        pass

    @abstractmethod
    def get_chat_settings(
        self,
        model_type: ChatModel,
        response_format: ResponseFormat
    ):
        pass

    @abstractmethod
    def transform_messages(self, model_type: ChatModel, messages: List[Message]):
        pass

    @abstractmethod
    def run(
        self,
        model_type: ChatModel,
        system_msg: str,
        messages: List[Message],
        max_tokens: int = 4000,
        temperature: float = 0.4,
        tools: List[Tool] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT
    ):
        pass
