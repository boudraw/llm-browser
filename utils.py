from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from html_utils import create_xpath_selector_from_description


def scroll_offset(driver, offset):
    # Adjust from current scroll position
    scroll_y = driver.execute_script("return window.scrollY")
    # Use JavaScript to scroll to the adjusted position
    driver.execute_script(f"window.scrollTo(0, {scroll_y + offset});")
    return True


def scroll_down_half_page(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight") // 2
    scroll_offset(driver, screen_height)
    return True


def scroll_down_page(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight")
    scroll_offset(driver, screen_height)
    return True


def scroll_up_half_page(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight") // 2
    scroll_offset(driver, -screen_height)
    return True


def scroll_up_page(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight")
    scroll_offset(driver, -screen_height)
    return True


def scroll_to_bottom(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight")
    scroll_offset(driver, screen_height)
    return True


def scroll_to_top(driver):
    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight")
    scroll_offset(driver, -screen_height)
    return True


def scroll_to(driver, element):
    # Get the coordinates of the element
    x = element.location['x']
    y = element.location['y']

    # Get the screen height using JavaScript and divide it by 2
    screen_height = driver.execute_script("return window.innerHeight") // 2

    # Adjust the y coordinate of the element to align in the middle of the page
    middle_y = y - screen_height

    # Use JavaScript to scroll to the adjusted position
    driver.execute_script(f"window.scrollTo({x}, {middle_y});")
    return True


def get_element_by_label(driver, label_text):
    # Find the label with the provided text
    label = locate(driver, By.XPATH, f'//label[text()="{label_text}"]')

    # Get the 'for' attribute of the label, which should match the 'id' of the associated input
    input_id = label.get_attribute('for')

    # Find the input field by its id
    element = locate(driver, By.ID, input_id)
    return element


def locate(driver, element_type, selector, wait_time=5, max_tries=2, ec=EC.presence_of_all_elements_located, return_single=True, raise_exception=False, description='NOT SPECIFIED'):
    elements = None
    tries = 0
    while elements is None and tries < max_tries:
        try:
            elements = WebDriverWait(driver, wait_time).until(
                ec((element_type, selector))
            )
        except TimeoutException:
            tries += 1

    if raise_exception and not elements:
        raise Exception(f"Could not locate {description}")

    if not elements:
        return None if return_single else []

    # Return a single element if only one is found or if return_single is True, otherwise return the list
    return elements[0] if return_single and len(elements) == 1 else elements


def wait_for_url_change(driver, interval=5):
    current_url = driver.current_url

    while current_url != driver.current_url:
        time.sleep(interval)

    return True


def click_on_coords(driver, x, y):
    driver.execute_script(f"window.scrollTo({x}, {y});")
    driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
    return True


# def locate_element_using_natural_language(driver, description):
#     xpath_selector = create_xpath_selector_from_description(driver, description)
#     element = locate(driver, By.XPATH, xpath_selector, description=description)
#     return element


def run_code(driver, code):
    exec(code)
    return True
