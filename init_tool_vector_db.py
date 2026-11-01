from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams,Distance

PROJECT_DIR = Path(__file__).resolve().parent
COLLECTION_NAME = "tool_usage_docs"

client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=2048,distance = Distance.COSINE),
    )

info = client.get_collection(COLLECTION_NAME)
print("向量维度",info.config.params.vectors.size)
total = client.count(collection_name=COLLECTION_NAME).count
print("片段数量:",total)

client.close()
