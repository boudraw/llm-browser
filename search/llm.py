from search.web import search_google
from chat.message import Message, ChatModel, ResponseFormat
from chat.tool import Tool, ToolParameter


def search(provider, query, messages: list = None):
    if not messages:
        messages = []

    search_tool = Tool("search", "Searches Google for any query!", [ToolParameter("query", "str", "The query to punch in Google.")], search_google)
    return provider.run(
            model_type=ChatModel.SUPER,
            system_msg="You are an AI agent that assists users in finding information online. If you already have information from Context, use that before searching",
            messages=messages + [Message(query, "user", "text")],
            response_format=ResponseFormat.FUNCTION_CALLS,
            tools=[search_tool]
        )
