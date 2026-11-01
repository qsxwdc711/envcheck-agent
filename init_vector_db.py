from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams,Distance

PROJECT_DIR = Path(__file__).resolve().parent

client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
if not client.collection_exists("envcheck_sop"):
    client.create_collection(
        collection_name="envcheck_sop",
        vectors_config=VectorParams(size=2048,distance = Distance.COSINE),
    )

info = client.get_collection("envcheck_sop")
print("向量维度",info.config.params.vectors.size)
total = client.count(collection_name="envcheck_sop").count
print("片段数量:",total)

client.close()
