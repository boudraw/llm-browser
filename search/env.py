from environs import Env

env = Env()
env.read_env()

SERPER_API_KEY = env("SERPER_API_KEY", None)
SERPER_URL = "https://google.serper.dev/search"
