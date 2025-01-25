import logging
from browser.driver import create_driver
from browser.ingest import ingest_page
from chat.message import Message
from memory.embeddings import EmbeddingModel, EmbeddingMemory
from memory.tags import TagMemory
from environs import Env
from providers.anthropic import Anthropic
from providers.open_ai import OpenAI
from search.llm import search
from browser.task import complete_browsing_query

env = Env()
env.read_env()

ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", None)
OPENAI_API_KEY = env("OPENAI_API_KEY", None)


def choose_provider():
    if OPENAI_API_KEY and ANTHROPIC_API_KEY:
        decision = input("Which provider would you like to use? (openai/anthropic):\n")
        if decision == "O" or decision == "o" or decision == "openai":
            return OpenAI(OPENAI_API_KEY)
        elif decision == "A" or decision == "a" or decision == "anthropic":
            return Anthropic(ANTHROPIC_API_KEY)
        else:
            return choose_provider()
    elif OPENAI_API_KEY:
        return OpenAI(OPENAI_API_KEY)
    elif ANTHROPIC_API_KEY:
        return Anthropic(ANTHROPIC_API_KEY)
    else:
        exit("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment variables.")


def create_providers():
    if OPENAI_API_KEY and ANTHROPIC_API_KEY:
        return OpenAI(OPENAI_API_KEY), Anthropic(ANTHROPIC_API_KEY)
    else:
        exit("Please set OPENAI_API_KEY and ANTHROPIC_API_KEY in your environment variables.")


def teach(provider, tags_memory, embedding_memory, text):
    embedding = provider.vectorize(text, 512, EmbeddingModel.ADVANCED)
    tags_memory.insert_tags_relations(embedding.tags)
    embedding_memory.add_embeddings([embedding])
    return embedding


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("simple-cli.log"),
            logging.StreamHandler()
        ]
    )
    openai, anthropic = create_providers()
    embedding_memory = EmbeddingMemory("llm-browser", env("PINECONE_API_KEY", None))
    if not embedding_memory:
        exit("Please set PINECONE_API_KEY in your environment variables.")

    tags_memory = TagMemory()
    query = input("Assistant: Hey there! How can I help?\n")
    messages = []
    if query.startswith("ingest||"):
        driver = create_driver(query.split("||")[1])
        ingest_page(driver, openai, tags_memory, embedding_memory)

    # while True:
    #     user_embedding = openai.vectorize(messages[-1].content + " - " + query, 512, EmbeddingModel.ADVANCED)
    #     search_embeddings = embedding_memory.search_embeddings(user_embedding)
    #     messages = messages + [Message("Context:\n\n"+"\n-----------------\n".join([embedding.text for embedding in search_embeddings]), "user", "text")]
    #     search_result = search(openai, query, messages)
    #     teach(openai, tags_memory, embedding_memory, search_result)
    #     query = input(f"Assistant: {search_result}\n")
    #     messages = messages + [Message(search_result, "assistant", "text"), Message(query, "user", "text")]

    driver = create_driver("https://www.google.com")
    while True:  # Kill with CTRL+C
        response = complete_browsing_query(openai, driver, query, messages)
        messages.append(Message(query, "user", "text"))
        messages.append(Message(response, "assistant", "text"))
        query = input("Assistant: " + response + "\nYou: ")
