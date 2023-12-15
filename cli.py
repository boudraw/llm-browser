import typer
from llm import run_web_task
from planner import generate_steps, generate_task_from_steps
from checker import check_plan_step
from driver import create_driver
import logging

app = typer.Typer()


@app.command()
def browse():
    driver = create_driver("https://google.com")
    messages = []
    task = typer.prompt("Hey there! How can I help?\n")
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": task},
        ]
    })
    while True:
        response = complete_browsing_task(driver, task, messages)
        messages.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": response},
            ]
        })

        task = input(response+"\n: ")
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": task},
            ]
        })


def complete_browsing_task(driver, task: str, messages=None):
    steps = generate_steps(task, messages)
    plan = "Plan: \n"

    for index, step in enumerate(steps):
        plan += f"{index+1}. {step}\n"

    logging.debug(plan)

    while len(steps) > 0:
        step = steps[0]
        step_task = generate_task_from_steps(step, task)
        step_response, new_driver = run_web_task(step_task, messages, driver)
        if not driver:
            driver = new_driver

        is_step_finished, is_goal_finished = check_plan_step(driver, step, task, [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": plan},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": step_response},
                ],
            }
        ])

        logging.debug("Step finished: " + str(is_step_finished))
        logging.debug("Goal finished: " + str(is_goal_finished))

        if is_goal_finished:
            return step_response

        if not is_step_finished:
            steps.insert(0, step)
            continue
        else:
            del steps[0]


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("cli.log"),
            logging.StreamHandler()
        ]
    )
    app()
