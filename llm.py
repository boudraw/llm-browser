import json, base64
from openai import OpenAI
from env import OPENAI_API_KEY, DEBUG
from utils import run_code
from driver import create_driver

client = OpenAI(api_key=OPENAI_API_KEY)


def get_utils_code():
    utils_code = open("./utils.py", "r")
    return utils_code.read()


TASK_GENERATION = """You are an expert in Selenium python.
An AI designed to receive a task's goal and create all of the steps necessary to reach the goal.
You will be given a goal and you will need to create all of the Selenium code calls necessary to reach the goal.

You will work in a step by step approach
You have to work one step at a time, feel free to search for stuff before reaching a conclusion.

First step should be to Google something if an explicit link is not provided.
Please try to google like an average human and don't use extended search functionalities
(like site:example.com AVOID THAT UNLESS YOU'RE 100% right).
After every step, you will be given the site's screenshot and you will need to create the next step.

The driver instance will be created outside of the code you provide and will be kept the same throughout all the steps.
The code you provide will be finalized and require no extra modifications (it will run using run_code).
Make sure to always wrap python code in ```python and ``` to make sure it is formatted correctly.

IMPORTANT: On only the first message, return a JSON of the first link you'd like to navigate to.
Example: {"initial_url": "https://google.com"}
When you have enough information to complete the task, ALWAYS return the following JSON object:
{"done": "This is your example answer here about the goal status or to answer any questions!"}

Tip:
If you plan to search on google go straight to the search results page.
Example: https://www.google.com/search?q=how+to+use+selenium+python

The following is a utility file that you can use to create the driver and other utilities.
Only use the functions in the utils.py file, and only import what's missing from utils.py.

IMPORTANT:
- When being questioned about cookies, always accept them!
- THE USER HAS NO KNOWLEDGE ABOUT THE WEB BROWSER SO DON'T ASK THEM TO DO ANYTHING!
- Whenever outputting JSON, don't wrap it in anything, just return the JSON object.
- Never make up links, if you don't know something, relay that to the user.
- Try to click using coordinates as least as possible, only as a last resort.
- You will only be given visual info, so you will need to use that to find elements. Never ask for HTML, you can't have any.
- XPATH is the most reliable way to find elements!
    Try to be as generic as possible.
    Don't assume the element type or tag name.
    Search mostly via text even if it means clicking on multiple wrong things, before getting to the right one!
    Use XPATH whenever possible.
    Use the Selenium native way whenever possible. don't try hacks like executing JS to click on something.
    IMPORTANT: ALWAYS assume that multiple, none or a single item(s) will be returned and code for that by looping for clicks, etc!!!
    
    Example:
    
    What not to do:
    ```python
    # Click on the "Accept all" button for cookies to proceed with the search results
    accept_cookies_button = locate(driver, By.XPATH, "//div[contains(text(),'Accept all')]", description='Accept all cookies button')
    accept_cookies_button.click()
    ```
    
    What to do:
    ```python
    # Click on the "Accept all" button for cookies to proceed with the search results
    accept_cookies_button = locate(driver, By.XPATH, "//div[contains(text(),'Accept all')]", description='Accept all cookies button')
    if accept_cookies_button is None:
        # If the button is not found, assume that the implementation is faulty, try again :(
    if isinstance(accept_cookies_button, list):
        for button in accept_cookies_button:
            button.click()
    else:
        accept_cookies_button.click()
    ```

""" + f"""
Utils file:
{get_utils_code()}
"""


def run_web_task(task: str, messages=None, driver=None):
    if messages is None:
        messages = [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": TASK_GENERATION},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": task},
                    ],
                }
            ]

    if DEBUG:
        print("Running LLM Query...")
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        temperature=0.2,
        top_p=1,
        max_tokens=4096,
        messages=messages
    )
    message = response.choices[0].message.content

    if DEBUG:
        print("LLM Response: " + message)

    # Try to parse JSON
    try:
        json_data = json.loads(message)
    except:
        json_data = None

    # Try to parse python code
    try:
        python_code = message.split("```python")[1].split("```")[0]
    except:
        python_code = None

    if json_data is not None and "done" in json_data:
        return json_data["done"]
    elif json_data is not None and "initial_url" in json_data:
        initial_url = json_data["initial_url"]
        driver_id, driver = create_driver(initial_url)
    elif python_code is not None:
        try:
            run_code(driver, python_code)
        except Exception as e:
            messages.append(
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "Error: " + str(e)},
                    ],
                }
            )
            return run_web_task(task, messages, driver)

    if driver is None:
        return run_web_task(task, messages, driver)

    # html_content = driver.page_source  # Use your Selenium driver's page source
    # soup = BeautifulSoup(html_content, 'html.parser')
    #
    # max_depth = 0  # Adjust the depth as needed
    # limited_body_content = list(extract_to_depth(soup.body, max_depth))
    #
    # # Apply visibility and relevance filter
    # relevant_visible_elements = filter(is_relevant_and_visible, limited_body_content)
    # relevant_visible_html = ''.join(str(tag) for tag in relevant_visible_elements if not isinstance(tag, str))
    # messages.append(
    #     {
    #         "role": "system",
    #         "content": [
    #             {"type": "text", "text": "Scraping Output!\nHTML:\n\n" + relevant_visible_html},
    #         ],
    #     }
    # )

    messages.append(
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": message},
            ],
        }
    )

    screenshot_path = "screenshot.png"
    driver.save_screenshot(screenshot_path)
    with open(screenshot_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    base64_screenshot = f"data:image/png;base64,{encoded_string}"
    messages.append(
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
        }
    )

    return run_web_task(task, messages, driver)


if __name__ == '__main__':
    while True:
        task = input("Enter a task: ")
        output = run_web_task(task)
        print("Task Output: " + output)