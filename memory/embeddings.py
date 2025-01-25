from enum import Enum
from pinecone import Pinecone
from uuid import uuid4
from typing import List, Dict, AnyStr


class EmbeddingModel(Enum):
    BASE = "vector_base"
    ADVANCED = "vector_medium"
    SUPER = "vector_advanced"


class Embedding:
    def __init__(
        self,
            model_type: EmbeddingModel,
            text: str,
            dimensions: int,
            vectors: List[float],
            tags: List[str] = None,
            metadata: dict = None
    ) -> object:
        self.text = text
        self.dimensions = dimensions
        self.model_type = model_type
        self.vectors = vectors
        self.tags = tags
        self.metadata = metadata


def embedding2pinecone(embedding: Embedding) -> Dict:
    return {
        "id": str(uuid4()),
        "values": embedding.vectors,
        "metadata": {
            "model_type": embedding.model_type.value,
            "text": embedding.text,
            "tags": embedding.tags,
        }
    }


def pinecone2embedding(pinecone: Dict) -> Embedding:
    return Embedding(
        model_type=EmbeddingModel(pinecone["metadata"]["model_type"]),
        text=pinecone["metadata"]["text"],
        dimensions=len(pinecone["values"]),
        vectors=pinecone["values"],
        tags=pinecone['metadata']['tags'],
        metadata={k: v for k, v in pinecone["metadata"].items() if k not in ["model_type", "text", "tags"]}
    )


def pinecone2tag_embedding(pinecone: Dict) -> (str, Embedding):
    return pinecone["id"], Embedding(
        model_type=EmbeddingModel.BASE,
        text=pinecone["id"],
        dimensions=len(pinecone["values"]),
        vectors=pinecone["values"],
        metadata=pinecone["metadata"]
    )


def tag_embedding2pinecone(tag: str, embedding: Embedding) -> Dict:
    return {
        "id": tag,
        "values": embedding.vectors
    }

pinecone_client = None


class EmbeddingMemory:
    def __init__(self, index_name: str, api_key: str):
        global pinecone_client
        if not pinecone_client and api_key:
            pinecone_client = Pinecone(api_key=api_key)
        if not pinecone_client:
            raise ValueError("Pinecone API Key is required at least once.")
        self.index = pinecone_client.Index(index_name)
        # self.tag_index = pinecone_client.Index("tags")

    def add_tags(self, tag_embedding_tuples: list):
        tags = [tag_embedding2pinecone(tag, embedding) for tag, embedding in tag_embedding_tuples]
        self.index.upsert(
            vectors=tags
        )

    def add_embeddings(self, embeddings: List[Embedding]):
        vectors = [embedding2pinecone(embedding) for embedding in embeddings]
        self.index.upsert(
            vectors=vectors
        )

    def search_embeddings(self, embedding: Embedding, k: int = 25) -> List[Embedding]:
        results = self.index.query(
            vector=embedding.vectors,
            top_k=k,
            include_values=True,
            include_metadata=True
        )
        if results.matches is None:
            return []

        return [pinecone2embedding(result) for result in results.matches if (result['score'] > 0.5)]


    # def search_tags(self, vectors: str, k: int = 10) -> List[Embedding]:
    #     results = self.tag_index.query(
    #         vector=vectors,
    #         top_k=k,
    #         include_values=True,
    #         include_metadata=True
    #     )
    #     return [pinecone2tag_embedding(result) for result in results.items]
