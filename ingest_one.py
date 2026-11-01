import json
from pathlib import Path
from qdrant_client.models import PointStruct
import asyncio
from qdrant_client import QdrantClient
from app.embedding_client import embed_text
PROJECT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = PROJECT_DIR /"data"/"docs"/"kernel_check.json"
async def main():
    with open(FIXTURES_DIR,"r",encoding = "utf-8")as file:
        chunk = json.load(file)
    vector = await embed_text(chunk["content"])
    if len(vector)!=2048:
        raise ValueError("向量维度与集合配置不一致")
    client = QdrantClient(
    path=str(PROJECT_DIR / ".data" / "qdrant")
)
    try:
        point = PointStruct(
        id=1,
        vector=vector,
        payload=chunk,
    )
        client.upsert(
        collection_name="envcheck_sop",
        points=[point],
        wait=True,
    )
        saved = client.retrieve(
        collection_name="envcheck_sop",
        ids=[1],
        with_payload=True,
    )
    finally:
        client.close()
    print("读回片段:",saved[0].payload["chunk_id"])
if __name__ =="__main__":
    asyncio.run(main())
