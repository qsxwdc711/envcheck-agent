from pathlib import Path
from app.retrieval import DB_LOCK
from qdrant_client import QdrantClient, models

PROJECT_DIR = Path(__file__).resolve().parents[1]

def search_tool_chunks(query_vector:list[float],tool_name:str,limit:int=3)->list[dict]:
    if len(query_vector)!=2048:
        raise ValueError("向量维度与集合配置不一致")
    with DB_LOCK:
        client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
        try:
            response = client.query_points(
            collection_name="tool_usage_docs",
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tool_name",
                        match=models.MatchValue(value=tool_name),
                    )
                ]
            ),
            )
            return [hit.payload for hit in response.points]
        finally:
            client.close()
