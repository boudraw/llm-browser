from env import client
from planner import generate_task_from_steps
from driver import get_screenshot_base64
import json


def check_plan_step(driver, step_description: str, task: str, messages=None):
    base64_screenshot = get_screenshot_base64(driver)
    if messages is None:
        messages = []
    CHECKER_PROMPT = """You are part of a web browser.
Your job is QA.
You take in a screenshot of the website, the general goal, the plan, and the current step.
You output whether the current step is correct or not.
You also output whether the plan is fully finished preemptively or not.

Output a JSON object like the following:
```json
{"is_current_step_correct": true, "is_plan_finished": true}
```

If the current step is 100% correct, and you have proof, set is_current_step_correct to true, otherwise set it to false.
If the plan is finished;
    if you have more than enough information to answer the original question, and you satisfy the plan's intentions
, set is_plan_finished to true, otherwise set it to false.
"""
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": CHECKER_PROMPT},
            ],
        },
        {
            "role": "system",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_screenshot,
                        "detail": "high"
                    }
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": generate_task_from_steps(step_description, task)},
            ],
        }
    ] + messages
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        temperature=0,
        top_p=1,
        max_tokens=4096,
        messages=messages
    )
    message = response.choices[0].message.content
    obj = json.loads(message.split("```json")[1].split("```")[0])
    return obj["is_current_step_correct"], obj["is_plan_finished"]


def check_if_stuck(last_n_messages):
    CHECKER_PROMPT = """You are an integral component of a web browser, specializing in Quality Assurance (QA).
Your primary function is to monitor the AI-driven web browsing process, ensuring smooth operation.
Your specific task involves checking for any instances where the browser becomes unresponsive or "stuck."
This is identified by observing if there is a repetition of identical messages.

Your outputs are formatted in JSON, comprising two key elements:

YOU SHOULD AVOID FLAGGING THE BROWSER AS STUCK UNLESS YOU ARE CERTAIN THAT IT IS.

is_stuck (Boolean): Indicates whether the browser is stuck.
stuck_message (String): Provides a helpful message to the user in case the browser is stuck.
This message should offer guidance and a suggested action to assist in resolving the issue.
It is crucial that your responses remain general and do not reveal any underlying AI or specific technologies like Selenium.
Your communications should be framed as seeking user assistance in a situation where you are unable to proceed.

Example outputs:

When stuck: {"is_stuck": true, "stuck_message": "Explain why stuck, make questions HERE"}
When not stuck: {"is_stuck": false, "stuck_message": null}
"""
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": CHECKER_PROMPT},
            ],
        },
    ] + last_n_messages
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0,
        top_p=1,
        max_tokens=4096,
        response_format={"type": "json_object"},
        messages=messages
    )
    message = response.choices[0].message.content
    obj = json.loads(message)
    return bool(obj["is_stuck"]), str(obj["stuck_message"])
