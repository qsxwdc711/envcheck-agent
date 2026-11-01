from app.rag_client import answer_question
import asyncio
from pathlib import Path
from qdrant_client import QdrantClient
from app.embedding_client import embed_text
PROJECT_DIR = Path(__file__).resolve().parent
async def main():
    question = "这批服务器验收要求的具体内核版本号是多少？"
    query_vector = await embed_text(question)
    if len(query_vector)!=2048:
        raise ValueError("向量维度与集合配置不一致")
    print("查询向量维度：", len(query_vector))
    client = QdrantClient(path=str(PROJECT_DIR / ".data" / "qdrant"))
    try:
        response = client.query_points(
            collection_name="envcheck_sop",
            query=query_vector,
            limit=3,
            with_payload=True,
            with_vectors=False,
        )
    finally:
        client.close()
    for hit in response.points:
        print(hit.payload["chunk_id"], hit.score, hit.payload["section"])
        print(hit.payload["content"])
    chunks = [hit.payload for hit in response.points]
    answer = await answer_question(question, chunks)
    print(answer.model_dump_json(indent=2))
if __name__ == "__main__":
    asyncio.run(main())
