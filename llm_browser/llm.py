import json, logging, os
from llm_browser.env import client
from llm_browser.utils import run_code
from llm_browser.driver import create_driver, get_screenshot_base64
from llm_browser.checker import check_if_stuck


def get_utils_code():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    utils_filepath = os.path.join(current_dir, "utils.py")
    utils_code = open(utils_filepath, "r")
    return utils_code.read()


BROWSER_PROMPT = """You are an expert in Selenium python.
You receive a goal and create & execute all of the steps necessary to reach the goal.
You will need to create all of the Selenium code calls necessary to reach the goal.

You will work in a step by step approach.

First step should be to Google something if an explicit link is not provided.
Please try to google like an average human and don't use extended search functionalities
(like site:example.com AVOID THAT UNLESS YOU'RE 100% right).
After every step, you will be given the site's screenshot and you will need to create the next step.

The driver instance will be created outside of the code you provide and will be kept the same throughout all the steps.
The code you provide will be finalized and require no extra modifications (it will run using run_code).
Make sure to always wrap python code in ```python and ``` to make sure it is formatted correctly.
Make sure to always wrap JSON in ```json and ``` to make sure it is formatted correctly.

IMPORTANT: You can navigate to any URL by outputting the following JSON object:
Example: 
```json
{"url": "https://google.com"}
```

Tip:
If you plan to search on google go straight to the search results page.
Example URL: https://www.google.com/search?q=how+to+use+selenium+python
 
IMPORTANT:
- THE SCREENSHOT IS THE SINGLE SOURCE OF TRUTH. It's the most up-to-date info you have.
- Don't assume any information that's outside of the screenshot.
- !!!!!!!!!!!NEVER EVER WRITE is_visible - is_displayed checks NO MATTER WHAT!!!!!!!!!!!!!
Instead of:
# If multiple elements are found, click the first one that is visible
for button in accept_cookies_button:
    if button.is_displayed():
        button.click()
        break
DO:
# If multiple elements are found, click the first one that is visible
for button in accept_cookies_button:
    button.click()
    break
    
    
- Always try to combine multiple steps at once if you can code all of the edge cases!
- Scroll, if you need to!
- If you get stuck, try to take a step back, and try a different approach!
- Avoid using hardcoded classes, IDs, etc. Try to use text as much as possible!
- When being questioned about cookies, always accept them!
- Expect some of the elements to be inside iframes.
- Try to reverse engineer the website (structurally), and write code to debug and get more info. 
- THE USER HAS NO KNOWLEDGE ABOUT THE WEB BROWSER SO DON'T ASK THEM TO INTERACT!
- Never make up links, if you don't know something, communicate that to the user.
- You will only be given visual info, so you will need to use the screenshot to create code to locate elements.
- If you're not progressing, that probably means you have a bug in your code, try to debug it!
- XPATH is the most reliable way to find elements!
    Try to be as specific as possible.
    DO NOT ASSUME ANY element classes, IDs, siblings, parents, etc.
    Search only via text even if it means clicking on multiple wrong things, before getting to the right one!
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
    accept_cookies_button = locate(driver, By.XPATH, "//*[contains(text(),'Accept all')]", description='Accept all cookies button')
    if accept_cookies_button is None:
        # If the button is not found, assume that the implementation is faulty, try again :(
    if isinstance(accept_cookies_button, list):
        for button in accept_cookies_button:
            button.click()
    else:
        accept_cookies_button.click()
    ```


    What not to do:
    first_link = locate(driver, By.XPATH, "(//div[@class='tF2Cxc']//a)[1]", description='the first search result link')
    
    What to do:
    first_link = locate(driver, By.XPATH, "//*[contains(text(), 'Text') and contains(text(), 'link')]", description='Text from the 3 first links', return_single=False)


You should try and answer the original question or task's goal as soon as you have enough info.
When you have enough information to complete the task, return the following JSON object:
```json
{"done": "This is your example answer about the goal's status or to answer any question(s)!"}
```

The following is a utility file that you can use to create the driver and other utilities.
Only use the functions in the utils.py file, and only import what's missing from utils.py.

""" + f"""
Utils file:
{get_utils_code()}
"""


def run_web_task(task: str, messages=None, driver=None, counter=0):
    if messages is None:
        messages = []

    if driver is None:
        driver = create_driver("https://google.com")

    base64_screenshot = get_screenshot_base64(driver)

    system_messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": BROWSER_PROMPT},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": task},
                ],
            }
        ]

    screenshot_msg = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "The next section is the latest visual state of the browser, taken from a screenshot!"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_screenshot,
                        "detail": "low"
                    }
                },
            ],
        },
    ]
    latest_n_messages = 4
    most_recent_messages = messages[-latest_n_messages:]

    if counter % latest_n_messages == 0 and counter >= latest_n_messages:
        logging.debug("Checking if the AI is stuck...")
        is_stuck, stuck_msg = check_if_stuck(most_recent_messages)
        if is_stuck:
            logging.warn(stuck_msg)
            return run_web_task(task, [], driver, counter+1)
        else:
            logging.debug("AI is not stuck!")

    logging.debug("Running LLM Query...")
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        temperature=0,
        top_p=0.95,
        max_tokens=4096,
        messages=system_messages+most_recent_messages+screenshot_msg
    )
    message = response.choices[0].message.content

    logging.debug("LLM Response: " + message)

    # Try to parse JSON
    try:
        json_data = json.loads(message.split("```json")[1].split("```")[0])
    except:
        json_data = None

    # Try to parse python code
    try:
        python_code = message.split("```python")[1].split("```")[0]
    except:
        python_code = None

    if json_data is not None and "done" in json_data:
        return json_data["done"], driver
    elif json_data is not None and "url" in json_data:
        url = json_data["url"]
        driver.get(url)
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
            return run_web_task(task, messages, driver, counter+1)

    if driver is None:
        return run_web_task(task, messages, driver, counter+1)

    messages.append(
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": message},
            ],
        }
    )

    return run_web_task(task, messages, driver, counter+1)
