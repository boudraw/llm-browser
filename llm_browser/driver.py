import time, logging
from webdriver_manager.chrome import ChromeDriverManager
from seleniumwire.webdriver import Chrome as SW_Chrome
from llm_browser.env import PROXY_USERNAME, PROXY_PASSWORD, PROXY_HOST, PROXY_PORT, HEADLESS
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.driver_cache import DriverCacheManager
import platform, base64


def chrome_proxy() -> dict:
    options = {
        'disable_capture': True,
        'connection_keep_alive': True,
        'request_blocking': True,
        'block_domains': []
    }
    if not PROXY_PASSWORD or not PROXY_USERNAME or not PROXY_HOST or not PROXY_PORT:
        return options

    connection_str = f"{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

    options['proxy'] = {
        "http": f"http://{connection_str}",
        "https": f"http://{connection_str}",
        'no_proxy': 'localhost,127.0.0.1',
    }

    return options


def chrome_dns_over_https(endpoint: str) -> dict:
    dns_conf = {
        "dns_over_https.mode": "secure",
        "dns_over_https.templates": f"https://{endpoint}",
    }

    return dns_conf


def create_driver(initial_url: str):
    max_retries = 3
    retries = 0

    driver_id = str(int(time.time()))
    op = webdriver.ChromeOptions()
    op.page_load_strategy = 'eager'
    chrome_prefs = {}
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    op.experimental_options["prefs"] = chrome_prefs
    op.add_argument("--log-level=3")

    # Use the first profile found
    # chrome_user_data_dir = get_chrome_profile_dir()
    # first_profile = get_first_chrome_profile(chrome_user_data_dir)
    #
    # op.add_argument(f"user-data-dir={chrome_user_data_dir}")
    # op.add_argument(f"profile-directory={first_profile}")

    if HEADLESS:
        op.headless = True
        op.add_argument("--start-maximized")
        op.add_argument("--disable-blink-features=AutomationControlled")
        op.add_argument('--window-size=1600x900')
        op.add_argument('--disable-http2')
        op.add_argument(
            'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.106 Safari/537.36')
        op.add_argument('--no-sandbox')
        op.add_argument('--disable-extensions')
        op.add_argument('--disable-gpu')
        op.add_argument('--disable-dev-shm-usage')
        op.add_argument("--disable-browser-side-navigation")

    logging.debug("DRIVER INFO: Creating driver with URL " + initial_url)

    while retries < max_retries:
        try:
            proxy = chrome_proxy()

            if platform.system() == "Darwin":
                webdriver_service = Service()
                driver = SW_Chrome(service=webdriver_service, options=op, seleniumwire_options=proxy)  # Simplest form of driver for macOS
            else:
                cache_manager = DriverCacheManager(f"/tmp/llm-browser/{driver_id}/")
                latest_driver = ChromeDriverManager(driver_version="118.0.5993.70", cache_manager=cache_manager).install()

                dns_conf = chrome_dns_over_https("cloudflare-dns.com/dns-query")
                op.add_experimental_option('localState', dns_conf)

                webdriver_service = Service(latest_driver)
                driver = SW_Chrome(service=webdriver_service, options=op, seleniumwire_options=proxy)

            driver.set_page_load_timeout(100)

            # Test connection speed
            start_time = time.time()
            driver.get(initial_url)
            end_time = time.time()

            # If the page took more than 10 seconds to load, retry
            if end_time - start_time > 10:
                raise Exception("Connection too slow")

            logging.debug("Connection established in " + str(end_time - start_time) + " seconds")
            # If we got here, the connection is good
            return driver

        except Exception:
            logging.warn("Could not initialise driver, retrying...", exc_info=True)
            retries += 1
            try:
                driver.quit()  # Close the driver instance
            except NameError:  # If the driver wasn't created yet
                pass

    logging.error('Max retries reached. Cannot establish a good connection.')
    return False, False


def get_screenshot_base64(driver):
    time.sleep(1)
    screenshot_path = "screenshot.png"
    driver.save_screenshot(screenshot_path)
    with open(screenshot_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded_string}"
