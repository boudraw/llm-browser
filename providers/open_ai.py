from chat.provider import ProviderInterface
from chat.message import ChatModel, ResponseFormat, Message
from chat.formatter import MessageFormatter
from typing import List
from openai import OpenAI as OAI
from chat.tool import Tool
from memory.embeddings import EmbeddingModel, Embedding
from memory.tags import get_tags_context


class OpenAI(ProviderInterface):
    def __init__(self, api_key: str):
        self.client = OAI(api_key=api_key)

    def get_chat_model(self, model_type):
        if model_type == ChatModel.ADVANCED:
            return "gpt-3.5-turbo"
        elif model_type == ChatModel.SUPER:
            return "gpt-4o"
        elif model_type == ChatModel.MM_ADVANCED:
            return "gpt-4o"
        elif model_type == ChatModel.MM_SUPER:
            return "gpt-4o"
        else:
            raise ValueError("Invalid LLM Model Type")

    def get_chat_settings(
        self,
        model_type: ChatModel,
        response_format: ResponseFormat
    ):
        if response_format == ResponseFormat.JSON:
            return {
                "response_format": {
                    "type": "json_object"
                }
            }
        # BREAKS MessageFormatter

        return {}

    def transform_messages(self, model_type, messages):
        transformed_messages = []
        for message in messages:
            msg_type = None
            content = None

            if message.type == "text":
                msg_type = "text"
                content = message.content
            elif message.type == "image":
                if model_type not in [ChatModel.MM_ADVANCED, ChatModel.MM_SUPER]:
                    raise ValueError("Image messages are only supported for multimodal models")
                msg_type = "image_url"
                content = {"url": message.content, "detail": "high" if model_type == ChatModel.MM_SUPER else "low"}

            transformed_messages.append(
                {
                    "role": message.role,
                    "content": [
                        {"type": msg_type, msg_type: content},
                    ],
                }
            )
        return transformed_messages

    def get_vector_model(self, model_type):
        if model_type == EmbeddingModel.BASE:
            return "text-embedding-3-small"
        elif model_type == EmbeddingModel.ADVANCED:
            return "text-embedding-3-small"
        elif model_type == EmbeddingModel.SUPER:
            return "text-embedding-3-large"
        else:
            raise ValueError("Invalid Vector Model Type")

    def vectorize(
        self,
        text: str,
        dimensions: int,
        model_type: EmbeddingModel,
        metadata: dict = None
    ):
        model = self.get_vector_model(model_type)
        vectors = self.client.embeddings.create(
            model=model,
            input=text,
            dimensions=dimensions
        ).data[0].embedding

        tags = self.run(
            ChatModel.SUPER,
            get_tags_context(),
            [Message(text, "user", "text")],
            response_format=ResponseFormat.JSON
        )['tags']
        return Embedding(model_type, text, dimensions, vectors, tags, metadata)

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
        model = self.get_chat_model(model_type)
        transformed_messages = self.transform_messages(model_type, messages)
        formatter = MessageFormatter(tools)
        settings = self.get_chat_settings(model_type, response_format)
        system_messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_msg + formatter.system_context(response_format)},
                ],
            }
        ]

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=system_messages + transformed_messages,
            **settings
        )

        if response_format == ResponseFormat.FUNCTION_CALLS:
            response, function_calls = formatter.format_output(response.choices[0].message.content, response_format)
            if len(function_calls) > 0:
                results = [fc.invoke(tools) for fc in function_calls]

                messages.append(Message(response, "assistant", "text"))
                messages.append(Message(f"<function_results>\n{results}</function_results>", "assistant", "text"))

                return self.run(model_type, system_msg, messages, max_tokens, temperature, tools, response_format)

            return response

        return formatter.format_output(response.choices[0].message.content, response_format)
