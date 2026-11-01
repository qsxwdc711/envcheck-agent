import asyncio
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.embedding_client import embed_text
from uuid import NAMESPACE_URL, uuid5

PROJECT_DIR = Path(__file__).resolve().parent
COLLECTION_NAME = "tool_usage_docs"
CHUNKS_PATH = PROJECT_DIR / "data" / "tool_docs" / "nic_link_check_chunks.jsonl"

async def main(target_chunk_id: str | None = None):
    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    points = []

    for chunk in chunks:
        if target_chunk_id is not None and chunk["chunk_id"] != target_chunk_id:
            continue
        point_id = str(
            uuid5(
                NAMESPACE_URL,
                f"tool-usage:{chunk["tool_name"]}:{chunk['chunk_id']}",
            )
        )
        vector = await embed_text(chunk["content"])

        if len(vector) != 2048:
            raise ValueError("向量维度与集合配置不一致")

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=chunk,
            )
        )

        print(point_id, chunk["chunk_id"], len(vector))
    client = QdrantClient(
        path=str(PROJECT_DIR / ".data" / "qdrant")
)
    try:
        client.upsert(
            collection_name = COLLECTION_NAME,
            points=points,
            wait=True,
        )
        saved = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point.id for point in points],
            with_payload=True,
        )
    finally:
        client.close()
    for record in saved:
        print("id:",record.id,"读回片段:",record.payload["chunk_id"])
if __name__ == "__main__":
    asyncio.run(main())
