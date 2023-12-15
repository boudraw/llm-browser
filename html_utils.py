import numpy as np
import faiss
import tiktoken
import openai
import logging
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from driver import get_screenshot_base64

enc = tiktoken.encoding_for_model("text-embedding-ada-002")
HTML_CHUNK_MAX_TOKENS = 4096  # 4k tokens - theoretically can reach up to 5k
HTML_CHUNK_BUFFER_TOKENS = 1000  # 1k tokens


def get_faiss_from_html(html_code: str):
    soup = BeautifulSoup(html_code, 'html.parser')
    chunks = rec_split_chunk(soup, max_tokens=HTML_CHUNK_MAX_TOKENS)
    embeddings = []
    for chunk in chunks:
        embeddings.append(get_embedding_from_str(chunk))
    return chunks, get_faiss_index_from_embeddings(embeddings)


def stringify_element(element):
    if isinstance(element, NavigableString):
        return str(element)
    elif isinstance(element, Tag):
        return element.prettify()
    else:
        return ''


def rec_split_chunk(element, max_tokens):
    chunks = []
    current_chunk = ''
    current_tokens = 0

    if isinstance(element, NavigableString):
        return [str(element)]

    for child in element.contents:
        child_str = stringify_element(child)
        child_tokens = len(enc.encode(child_str))

        if child_tokens > max_tokens or current_tokens + child_tokens > max_tokens + HTML_CHUNK_BUFFER_TOKENS:
            # Recursively split large child
            child_chunks = rec_split_chunk(child, max_tokens)
            chunks.extend(child_chunks)
        elif current_tokens + child_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = child_str
            current_tokens = child_tokens
        else:
            current_chunk += child_str
            current_tokens += child_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def get_embedding_from_str(input_str: str):
    response = openai.embeddings.create(
        input=input_str,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def get_np_embeddings(embeddings):
    return np.array(embeddings).astype('float32')


def get_faiss_index_from_embeddings(embeddings):  # Assuming all embeddings have the same dimension
    embeddings_np = get_np_embeddings(embeddings)
    faiss.normalize_L2(embeddings_np)

    # Using IndexFlatIP for cosine similarity
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings_np)
    return index


def merge_chunks(chunks, indices):
    indices = indices[0][::-1]
    total_chunks = len(chunks)

    ## CHUNKING ISNT PROPERLY WORKING (Tokens over limit for each chunk)

    merged_chunks = "HTML Chunks:\n"
    for index in indices:
        chunk = chunks[index]
        chunk_text = f"Chunk ({index+1}/{total_chunks}):\n" + chunk + '\n\n'
        merged_chunks += chunk_text

    return merged_chunks


def generate_description_with_screenshot(driver, description):
    PROMPT = """Your job is to generate the most detailed and specific HTML description of an element you can come up with.
You will be given a screenshot of the website, and your job is to output text that will be used to query the HTML via kNN.
You will also be given a description of the element, and you should use that to help you generate the HTML description.
Use the screenshot as a reference, and try to be as specific as possible.
NEVER EVER say I don't know.
If you don't know, just make a very educated guess about the potential HTML structure.

Here is an example conversation:
- User:
button that says 'Accept all'
- You:
<button>Accept all</button>
"""

    base64_screenshot = get_screenshot_base64(driver)
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        temperature=0,
        top_p=1,
        max_tokens=4096,
        messages=[{
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": PROMPT
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_screenshot,
                        "detail": "low"
                    }
                }
            ],
        }, {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": description
                }
            ],
        }]
    )
    message = response.choices[0].message.content
    return message


def create_xpath_selector_from_description(driver, description: str, k=10):
    try:
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except TimeoutException:
        logging.warn("Timed out waiting for page to load")

    html_content = driver.execute_script("return document.documentElement.outerHTML;")
    description = generate_description_with_screenshot(driver, description)
    chunks, faiss_index = get_faiss_from_html(html_content)
    element_description_embeddings = get_np_embeddings([get_embedding_from_str(description)])
    distances, indices = faiss_index.search(element_description_embeddings, k)
    merged_chunks = merge_chunks(chunks, indices)
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0,
        top_p=1,
        max_tokens=4096,
        messages=[{
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": f"Please create an XPATH selector for the following element: {description}"
                },
                {
                    "type": "text",
                    "text": f"Here are the HTML chunks containing the element: {merged_chunks}"
                }
            ],
        }]
    )
    message = response.choices[0].message.content
    return message
