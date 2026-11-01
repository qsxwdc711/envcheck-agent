import asyncio
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.embedding_client import embed_text
DOCS = [
    (1, "kernel_check.json"),
    (2, "time_check.json"),
    (3, "gpu_info_check.json"),
]
PROJECT_DIR = Path(__file__).resolve().parent

async def main():
    points=[]
    for point_id,filename in DOCS:
        FIXTURES_DIR = PROJECT_DIR /"data"/"docs"/filename
        with open(FIXTURES_DIR,"r",encoding = "utf-8")as file:
            chunk = json.load(file)
        vector = await embed_text(chunk["content"])
        if len(vector)!=2048:
            raise ValueError("向量维度与集合配置不一致")
        points.append(
            PointStruct(id=point_id,vector=vector,payload=chunk)
        )
        print(point_id,chunk["chunk_id"],len(vector))
    client = QdrantClient(
        path=str(PROJECT_DIR / ".data" / "qdrant")
)
    try:
        client.upsert(
            collection_name = "envcheck_sop",
            points=points,
            wait=True,
        )
        saved = client.retrieve(
            collection_name="envcheck_sop",
            ids=[1,2,3],
            with_payload=True,
        )
    finally:
        client.close()
    for record in saved:
        print("id:",record.id,"读回片段:",record.payload["chunk_id"])
if __name__ == "__main__":
    asyncio.run(main())
