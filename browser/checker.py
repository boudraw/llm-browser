from chat.message import ChatModel, ResponseFormat


def check_plan_step(provider, messages):
    system_message = """You are a Google QA Automation Engineer.
You analyze 2 screenshots of a website together with a query.
The first screenshot is from before the plan was executed, and the second is after the plan was executed.
Your job is to confirm or deny that the plan has concluded.

Output a JSON object like the following:
```json
{"is_goal_reached": true/false}
```
"""
    obj = provider.run(
        system_msg=system_message,
        model_type=ChatModel.MM_SUPER,
        temperature=0.3,
        messages=messages,
        response_format=ResponseFormat.JSON
    )

    return obj["is_goal_reached"]
