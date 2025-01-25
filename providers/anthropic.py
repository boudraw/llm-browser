from chat.provider import ProviderInterface
from chat.message import ChatModel, ResponseFormat
from anthropic import Anthropic as ANT
from chat.formatter import MessageFormatter
from memory.embeddings import EmbeddingModel
from chat.message import Message
from typing import List
from chat.tool import Tool
import httpx
import base64


def extract_base64_image_info(base64_url):
    # Splitting the URL at the comma
    parts = base64_url.split(',')

    if len(parts) != 2:
        return None  # Invalid format

    # Extracting the metadata and the data
    metadata, data = parts
    # Extracting the image type from the metadata
    image_type = metadata.split(';')[0].split(':')[1]

    return image_type, data


def get_base64_image(url):
    try:
        # Fetch the image content using httpx
        with httpx.Client() as h_client:
            response = h_client.get(url)
            response.raise_for_status()  # This will raise an exception for HTTP error codes

        # Convert the image content to base64
        base64_image = base64.b64encode(response.content).decode()

        return base64_image
    except Exception as e:
        return f"An error occurred: {e}"


class Anthropic(ProviderInterface):

    def __init__(self, api_key: str):
        self.client = ANT(api_key=api_key)

    def get_chat_model(self, model_type):
        if model_type == ChatModel.ADVANCED:
            return "claude-3-sonnet-20240229"
        elif model_type == ChatModel.SUPER:
            return "claude-3-opus-20240229"
        elif model_type == ChatModel.MM_ADVANCED:
            return "claude-3-sonnet-20240229"
        elif model_type == ChatModel.MM_SUPER:
            return "claude-3-opus-20240229"
        else:
            raise ValueError("Invalid LLM Model Type")

    def get_chat_settings(
        self,
        model_type: ChatModel,
        response_format: ResponseFormat
    ):
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
                msg_type = "source"
                base_64 = message.content
                if message.content.startswith("http"):
                    base_64 = get_base64_image(message.content)
                image_type, data = extract_base64_image_info(base_64)
                content = {'type': "base64", "media_type": image_type, "data": data}

            if not transformed_messages or transformed_messages[-1]["role"] != message.role:
                transformed_messages.append({"role": message.role, "content": []})

            transformed_messages[-1]["content"].append(
                {"type": message.type, msg_type: content}
            )

        return transformed_messages

    def get_vector_model(self, model_type):
        pass

    def vectorize(
        self,
        text: str,
        dimensions: int,
        model_type: EmbeddingModel
    ):
        pass

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
        settings = self.get_chat_settings(model_type, response_format)
        formatter = MessageFormatter(tools)
        message = self.client.messages.create(
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg + formatter.system_context(response_format),
            messages=transformed_messages,
            model=model,
            **settings
        )

        if response_format == ResponseFormat.FUNCTION_CALLS:
            response, function_calls = formatter.format_output(message.content[0].text, response_format)
            if len(function_calls) > 0:
                results = [fc.invoke(tools) for fc in function_calls]

                messages.append(Message(response, "assistant", "text"))
                messages.append(Message(f"<function_results>\n{results}</function_results>", "assistant", "text"))

                return self.run(model_type, system_msg, messages, max_tokens, temperature, tools, response_format)

            return response

        return formatter.format_output(message.content[0].text, response_format)
