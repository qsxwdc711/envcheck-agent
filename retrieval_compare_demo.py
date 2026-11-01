import asyncio

from app.embedding_client import embed_text
from app.tool_retrieval import search_tool_chunks


async def main():
    question = "RoCE 线序检查的基础命令怎么写，需要提供哪些参数"
    query_vector = await embed_text(question)

    for limit in (3, 4, 7):
        chunks = await asyncio.to_thread(
            search_tool_chunks,
            query_vector,
            "nic_link_check",
            limit=limit,
        )
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        print(f"Top-{limit}:", chunk_ids)
        print("别名片段是否命中：", "nic-link-usage-003" in chunk_ids)


if __name__ == "__main__":
    asyncio.run(main())
