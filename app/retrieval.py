from pathlib import Path
from threading import Lock
from qdrant_client import QdrantClient, models

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_LOCK = Lock()

def search_chunks(query_vector:list[float],platform:str,limit:int=3)->list[dict]:
    if len(query_vector)!=2048:
        raise ValueError("向量维度与集合配置不一致")
    with DB_LOCK:
        client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
        try:
            response = client.query_points(
            collection_name="envcheck_sop",
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="platform",
                        match=models.MatchValue(value=platform),
                    )
                ]
            ),
            )
            return [hit.payload for hit in response.points]
        finally:
            client.close()
