import asyncio
from pathlib import Path
from qdrant_client import QdrantClient
from app.embedding_client import embed_text
PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = Path(__file__).resolve().parent

def main():
    client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
    try:
        client.set_payload(
            collection_name="envcheck_sop",
            payload={"platform": "nvidia"},
            points=[1, 2, 3],
            wait=True,
        )
        records = client.retrieve(
            collection_name="envcheck_sop",
            ids=[1, 2, 3],
            with_payload=True,
        )
        for record in records:
            print(
                record.id,
                record.payload["chunk_id"],
                record.payload["platform"],
            )
    finally:
        client.close()
if __name__ == "__main__":
    main()
