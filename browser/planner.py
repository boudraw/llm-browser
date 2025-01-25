from chat.message import ChatModel, Message, ResponseFormat
from browser.driver import get_screenshot_base64


def generate_steps(provider, driver, query=None):
    base64_screenshot = get_screenshot_base64(driver)
    system_message = """You will be given a query, and your job is to generate a JSON of the steps needed to reach the end goal.

You have access to a Selenium python instance where you can write code, and thus, the entire internet.
Assume the web browser driver instance is already open. 
If you plan to search on google, go straight to the search results page.
Example: https://www.google.com/search?q=how+to+use+selenium+python

The plan should accurately reflect the query's intentions, fully, without question.
Be as detailed as possible, ensure the plan is robust and can be followed by a QA Automation Engineer with no extra provided context.
Create a VERY ROBUST plan. Act like explaining in FULL-DETAIL to your CEO.

YOUR PLAN SHOULD ONLY INCLUDE INTERACTIONS AS STEPS, NO CHECKING OR WAITING FOR ELEMENTS TO APPEAR.

An example simplified conversation is shown below:
- User:
"Navigate to the latest MrBeast video on YouTube and tell me what the top comment is."
- You:
"{"1": "Navigate to https://www.google.com/search?q=MrBeast+channel", "2": "Click on the channel", "3": "Find the latest video by sorting", "4": "Click on it and output the top comment"}"
"""
    messages = [
        Message(query, "user", "text"),
        Message(base64_screenshot, "user", "image")
    ]

    obj = provider.run(
        model_type=ChatModel.MM_ADVANCED,
        system_msg=system_message,
        messages=messages,
        temperature=0.2,
        max_tokens=2048,
        response_format=ResponseFormat.JSON
    )

    return list(obj.values())


# TODO: Fix user asking for JSON output causing an infinite loop of messages

def generate_step_query_prompt(step: str, query: str):
    return f"""Query: {query}\nCurrent Step: {step}\n"""
