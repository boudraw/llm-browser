from browser.driver import get_screenshot_base64
from browser.planner import generate_steps, generate_step_query_prompt
from browser.checker import check_plan_step
from browser.utils import run_code
from chat.message import Message, ChatModel
import logging, os, json, time


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

Tip:
IF you're not making progress, try proceeding in a different way.
If you plan to search on google go straight to the search results page.
Example URL: https://www.google.com/search?q=how+to+use+selenium+python

IMPORTANT:

- If the plan's goal has been achieved, reply ONLY EXACTLY WITH: I AM DONE NOW!!!
- Assume everything on the latest screenshot is 100% accurate, no need to re-check for elements onscreen if visible in the screenshot.
- Write the code as if you're explaining it to a CEO. Make it do a lot of the steps at once and over-explain, before you implement the code.
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
- Expect some of the elements to be inside iframes.
- Try to reverse engineer the website (structurally), and write code to debug and get more info.
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


ALWAYS OUTPUT ONLY IN JSON OR PYTHON CODE!
EVERYTIME YOU CORRECTLY CHOOSE ILL TIP YOU 2k USD
ALWAYS WRAP BOTH PYTHON AND JSON WITH ```python AND ```json RESPECTIVELY
GROUP MULTIPLE STEPS INTO ONE WHEN YOU CAN

If you have context that might help out the user, reply as such: (each time you do it, you get $200)
```json
{"context": "Explanation of the info needed."}
```

The following is a utility file that you can use to create the driver and other utilities.
Only use the functions in the utils.py file, and only import what's missing from utils.py.

""" + f"""
Utils file:
{get_utils_code()}
"""

def get_visible_interactable_html(driver):
    # JavaScript to get visible and interactable elements, including text content
    js_code = """
    function isVisible(element) {
        return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
    }

    function isInteractable(element) {
        return element instanceof HTMLInputElement ||
               element instanceof HTMLButtonElement ||
               element instanceof HTMLSelectElement ||
               element instanceof HTMLAnchorElement ||
               element instanceof HTMLTextAreaElement ||
               element instanceof HTMLLabelElement ||
               element.hasAttribute('onclick') ||
               element.hasAttribute('href');
    }

    function getVisibleInteractableHtml(element) {
        let result = '';

        if (isVisible(element)) {
            if (isInteractable(element)) {
                result += element.outerHTML + '\\n';
            }

            Array.from(element.childNodes).forEach(child => {
                if (child.nodeType === Node.ELEMENT_NODE) {
                    result += getVisibleInteractableHtml(child);
                } else if (child.nodeType === Node.TEXT_NODE && isVisible(child.parentElement)) {
                    let text = child.textContent.trim();
                    if (text.length > 0) {
                        result += text + ' ';
                    }
                }
            });
        }

        return result;
    }

    return getVisibleInteractableHtml(document.body);
    """

    # Execute the JavaScript code
    filtered_html = driver.execute_script(js_code)
    return filtered_html


def execute_web_query(provider, driver, query: str, messages=None, counter=0):
    if messages is None:
        messages = []

    base64_screenshot = get_screenshot_base64(driver)
    page_html = get_visible_interactable_html(driver)

    context = [
        Message("Current page's filtered HTML (reference inside Python code):\n\n"+page_html, 'user', 'text'),
        Message(base64_screenshot, 'user', 'image')
    ]

    logging.debug("Running LLM Query...")
    message = provider.run(
        model_type=ChatModel.MM_SUPER,
        system_msg=BROWSER_PROMPT,
        temperature=0.5,
        messages=
        [Message(query, 'user', 'text')] + messages + context + [Message('Please continue.', 'user', 'text')]
    )
    messages.append(Message(message, "assistant", "text"))

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

    if json_data is not None:
        if "url" in json_data:
            url = json_data["url"]
            driver.get(url)
        elif "context" in json_data:
            return json_data["context"]
    elif python_code is not None:
        try:
            run_code(driver, python_code)
            return "Code executed successfully!\n\n" + python_code
        except Exception as e:
            messages.append(Message("Error while running the python code:\n" + str(e), "user", "text"))
            return execute_web_query(provider, driver, query, messages, counter+1)

    return execute_web_query(provider, driver, query, messages, counter+1)


def get_response_from_run(provider, messages):
    prompt = "You're talking to a 5-year-old. Always talk in past tense, and talk like you're the one taking action. Summarize the past conversation in simple terms."
    response = provider.run(
        model_type=ChatModel.MM_SUPER,
        system_msg=prompt,
        messages=messages,
        temperature=0.3
    )
    return response


def complete_browsing_query(provider, driver, query: str, messages=None):
    time.sleep(5)
    steps = generate_steps(provider, driver, query)
    beginning_screenshot = get_screenshot_base64(driver)
    plan = f"Original Query:\n{query}\n\nPlan:\n"

    for index, step in enumerate(steps):
        plan += f"{index+1}. {step}\n"
    if messages is None:
        messages = [Message(beginning_screenshot, "user", "image")]

    while True:
        step_response = execute_web_query(provider, driver, plan, messages)
        print(step_response)
        if step_response == 'I AM DONE NOW!!!':
            break
        messages.append(Message(step_response, "assistant", "text"))
        del steps[0]

    return get_response_from_run(provider, messages)