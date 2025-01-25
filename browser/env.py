from environs import Env

env = Env()
env.read_env()

PROXY_USERNAME = env("PROXY_USERNAME", None)
PROXY_PASSWORD = env("PROXY_PASSWORD", None)
PROXY_HOST = env("PROXY_HOST", None)
PROXY_PORT = env("PROXY_PORT", None)
HEADLESS = env("HEADLESS", False)
