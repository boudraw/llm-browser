from llm_browser.driver import create_driver
from llm_browser.browser import complete_browsing_task
import llm_browser.env as llm_env
import logging


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("simple-cli.log"),
            logging.StreamHandler()
        ]
    )
    messages = []

    if not llm_env.client:
        exit("Please set OPENAI_API_KEY in your environment variables.")

    driver = create_driver("https://google.com")
    task = typer.prompt("Hey there! How can I help?\n")
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": task},
        ]
    })
    while True:  # Kill with CTRL+C
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

