from llm_browser.env import client
import json


def generate_steps(task: str, messages=None):
    STEPS_PROMPT = """You are a world-renowned business professor at Stanford.
You will be given a question or task, and your job is to generate a JSON of the steps needed to reach the end goal.

You have access to a Selenium python instance where you can write code, and thus, the entire internet.
Assume the web browser driver instance is already open. 
If you plan to search on google, go straight to the search results page.
Example: https://www.google.com/search?q=how+to+use+selenium+python
Try to be really specific with all of your steps, and try to use as many steps as you think you need.

An example conversation is shown below:
- User:
"Navigate to the latest MrBeast video on YouTube and tell me what the top comment is."
- You:
"{1: "Navigate to https://www.google.com/search?q=MrBeast+channel", 2: "etc..." , 3: "etc..."}"
"""
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": STEPS_PROMPT},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": task},
            ],
        }
    ] + (messages or [])
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0,
        top_p=0.95,
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=messages
    )
    message = response.choices[0].message.content
    return list(json.loads(message).values())


# TODO: Fix user asking for JSON output causing an infinite loop of messages

def generate_task_from_steps(step: str, task: str):
    return f"""Task: {task}\nCurrent Step: {step}"""