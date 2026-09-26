from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os

# Global singleton instance to preserve in-memory data
_qdrant_instance = None


class QdrantStorage:
    def __init__(self, url=None, api_key=None, collection="docs", dim=384):
        """
        Initialize Qdrant client for Cloud or local usage.

        For Qdrant Cloud:
        - Set QDRANT_URL and QDRANT_API_KEY in your .env file
        - Or pass them as parameters

        For local Docker (if you get it working later):
        - url="http://localhost:6333", api_key=None

        Default dim=384 for all-MiniLM-L6-v2 model (free Sentence Transformers)
        Use dim=3072 for OpenAI text-embedding-3-large
        """
        global _qdrant_instance

        # Use singleton for in-memory database to persist data
        if _qdrant_instance is not None:
            self.client = _qdrant_instance
            self.collection = collection
            print(f"[Qdrant] Reusing existing in-memory database")
            return

        # Get credentials from environment or parameters
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")

        # Initialize client with fallback to in-memory
        try:
            if self.api_key and self.url:
                # Try Cloud connection first
                print(f"[Qdrant] Connecting to cloud: {self.url}")
                self.client = QdrantClient(
                    url=self.url, api_key=self.api_key, timeout=5
                )
                # Test connection
                self.client.get_collections()
                print(f"[Qdrant] Cloud connection successful")
            else:
                print(f"[Qdrant] No cloud credentials, using in-memory database")
                self.client = QdrantClient(location=":memory:")
                _qdrant_instance = self.client  # Save singleton
        except Exception as e:
            print(
                f"[Qdrant] Cloud connection failed ({str(e)}), falling back to in-memory database"
            )
            self.client = QdrantClient(location=":memory:")
            _qdrant_instance = self.client  # Save singleton

        self.collection = collection

        # Create collection if it doesn't exist
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                # distance=Distance.COSINE -> to calculate distances between two vector poins/dbs
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(self, ids, vectors, payloads):
        points = [
            PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
            for i in range(len(ids))
        ]
        self.client.upsert(self.collection, points=points)

    def search(self, query_vector, top_k: int = 5):
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            with_payload=True,
            limit=top_k,  # means for number of results to return
        ).points
        contexts = []
        sources = set()

        for r in results:
            payload = getattr(r, "payload", None) or {}
            text = payload.get("text", "")
            source = payload.get("source", "")
            if text:
                contexts.append(text)
                sources.add(source)

        return {"Context:-": contexts, "Sources:-": list(sources)}
