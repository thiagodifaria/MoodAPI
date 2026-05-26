import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class VectorDocument:
    id: str
    text: str
    sentiment: str
    confidence: float
    language: str
    metadata: dict[str, Any]


@lru_cache(maxsize=1)
def _load_embedding_model() -> tuple[Any, Any]:
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        settings.vector.embedding_model_name,
        cache_dir=settings.ml.model_cache_dir,
    )
    model = AutoModel.from_pretrained(
        settings.vector.embedding_model_name,
        cache_dir=settings.ml.model_cache_dir,
    )
    model.eval()
    return tokenizer, model


def build_text_embedding(text: str) -> list[float]:
    """Builds a real multilingual sentence embedding for semantic search."""
    import torch
    import torch.nn.functional as functional

    tokenizer, model = _load_embedding_model()
    encoded = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=min(settings.ml.max_text_length, 512),
        return_tensors="pt",
    )

    with torch.no_grad():
        output = model(**encoded)

    attention_mask = encoded["attention_mask"].unsqueeze(-1).expand(output.last_hidden_state.size()).float()
    summed = torch.sum(output.last_hidden_state * attention_mask, dim=1)
    counts = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
    embedding = functional.normalize(summed / counts, p=2, dim=1)[0]

    vector = [round(float(value), 8) for value in embedding.tolist()]
    if len(vector) != settings.vector.vector_size:
        raise RuntimeError(
            f"Embedding gerou {len(vector)} dimensoes, esperado {settings.vector.vector_size}"
        )
    return vector


class VectorSearchService:
    """Qdrant adapter with a deterministic embedding fallback."""

    def __init__(self) -> None:
        self._client: Any | None = None

    @property
    def enabled(self) -> bool:
        return settings.vector.enabled

    def _get_client(self) -> Any | None:
        if not self.enabled:
            return None

        if self._client is not None:
            return self._client

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams

            client = QdrantClient(url=settings.vector.url)
            collections = client.get_collections().collections
            names = {collection.name for collection in collections}

            if settings.vector.collection_name not in names:
                client.create_collection(
                    collection_name=settings.vector.collection_name,
                    vectors_config=VectorParams(
                        size=settings.vector.vector_size,
                        distance=Distance.COSINE,
                    ),
                )

            self._client = client
            return client
        except Exception as error:
            logger.warning("Vector DB indisponivel: %s", error)
            return None

    async def health(self) -> dict[str, Any]:
        client = self._get_client()
        return {
            "status": "healthy" if client is not None else "disabled" if not self.enabled else "degraded",
            "enabled": self.enabled,
            "provider": "qdrant",
            "collection": settings.vector.collection_name,
        }

    async def upsert(self, document: VectorDocument) -> bool:
        client = self._get_client()
        if client is None:
            return False

        try:
            from qdrant_client.http.models import PointStruct

            payload = {
                "text": document.text,
                "sentiment": document.sentiment,
                "confidence": document.confidence,
                "language": document.language,
                **document.metadata,
            }
            client.upsert(
                collection_name=settings.vector.collection_name,
                points=[
                    PointStruct(
                        id=document.id,
                        vector=build_text_embedding(document.text),
                        payload=payload,
                    )
                ],
                wait=True,
            )
            return True
        except Exception as error:
            logger.exception("Falha ao indexar vetor %s: %s", document.id, error)
            return False

    async def count(self) -> int:
        client = self._get_client()
        if client is None:
            return 0

        try:
            response = client.count(
                collection_name=settings.vector.collection_name,
                exact=True,
            )
            return int(response.count)
        except Exception as error:
            logger.exception("Falha ao contar vetores: %s", error)
            return 0

    async def upsert_many(self, documents: list[VectorDocument]) -> int:
        indexed = 0
        for document in documents:
            if await self.upsert(document):
                indexed += 1
        return indexed

    async def search(self, text: str, limit: int = 10) -> list[dict[str, Any]]:
        client = self._get_client()
        if client is None:
            return []

        try:
            response = client.query_points(
                collection_name=settings.vector.collection_name,
                query=build_text_embedding(text),
                limit=limit,
                with_payload=True,
                score_threshold=settings.vector.search_score_threshold,
            )
            results = response.points
            return [
                {
                    "id": str(result.id),
                    "score": float(result.score),
                    "payload": result.payload or {},
                }
                for result in results
            ]
        except Exception as error:
            logger.exception("Falha na busca vetorial: %s", error)
            raise


_vector_service = VectorSearchService()


def get_vector_service() -> VectorSearchService:
    return _vector_service
