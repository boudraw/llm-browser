from markdownify import markdownify
from memory.embeddings import EmbeddingModel
import time


def ingest_page(driver, provider, tags_memory, embedding_memory):
    time.sleep(2)
    md_html = markdownify(driver.page_source.split('</head>')[1])
    paragraphs = [p for p in md_html.split("\n\n\n\n\n") if p]
    for paragraph in paragraphs:
        print(paragraph)
        embedding = provider.vectorize(paragraph, 512, EmbeddingModel.ADVANCED)
        embedding_memory.add_embeddings([embedding])
        tags_memory.insert_tags_relations([(embedding.text, embedding)])

    return paragraphs