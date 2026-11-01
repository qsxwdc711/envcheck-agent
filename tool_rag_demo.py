import asyncio
from pathlib import Path
from qdrant_client import QdrantClient
from app.embedding_client import embed_text
from qdrant_client import QdrantClient, models
from app.tool_rag_client import answer_question
PROJECT_DIR = Path(__file__).resolve().parent
COLLECTION_NAME = "tool_usage_docs"
TOOL_NAME = "nic_link_check"
async def main():
    question = "RoCE 线序检查的基础命令怎么写，需要提供哪些参数？"
    query_vector = await embed_text(question)
    if len(query_vector)!=2048:
        raise ValueError("向量维度与集合配置不一致")
    print("查询向量维度：", len(query_vector))
    client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
    try:
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key = "tool_name",
                        match=models.MatchValue(value=TOOL_NAME),
                    )
                ]
            ),
            limit=3,
            with_payload=True,
            with_vectors=False,
        )
    finally:
        client.close()
    for hit in response.points:
        print(hit.payload["chunk_id"],
              hit.score,
              hit.payload["tool_name"],
              hit.payload["section"],
              )
        print(hit.payload["content"])
    chunks = [hit.payload for hit in response.points]
    answer = await answer_question(question, chunks)
    print(answer.model_dump_json(indent=2))
if __name__ == "__main__":
    asyncio.run(main())
