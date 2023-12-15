from environs import Env
from openai import OpenAI

env = Env()
env.read_env()  # Read .env file, if it exists


PROXY_USERNAME = env("PROXY_USERNAME", None)
PROXY_PASSWORD = env("PROXY_PASSWORD", None)
PROXY_HOST = env("PROXY_HOST", None)
PROXY_PORT = env("PROXY_PORT", None)
HEADLESS = env("HEADLESS", False)
OPENAI_API_KEY = env("OPENAI_API_KEY")
DEBUG = env("DEBUG", False)

client = OpenAI(api_key=OPENAI_API_KEY)
