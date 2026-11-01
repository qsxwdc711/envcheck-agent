from app.embedding_client import embed_text
from app.retrieval import search_chunks
import asyncio
from app.analyze import build_analysis_context, answer_inspection
from app.records import load_record
async def main(record_id = 1001,platform = "nvidia",question = "根据这条巡检记录，说明内核检查未通过的直接比较依据，并根据检索文档说明应该怎样复核。"):
    record =await asyncio.to_thread(load_record,record_id)
    question = "根据这条巡检记录，说明内核检查未通过的直接比较依据，并根据检索文档说明应该怎样复核。"
    query_vector = await embed_text(question)
    print("查询向量维度：", len(query_vector))
    platform = "nvidia"
    chunks = await asyncio.to_thread(
        search_chunks,
        query_vector,
        platform,
    )
    print("检索到的片段数：", len(chunks))
    for chunk in chunks:
        print(chunk["chunk_id"], chunk["section"])
    context = build_analysis_context(record, question, chunks)
    result = await answer_inspection(context)
    print(result.model_dump_json(indent=2))
if __name__ == "__main__":
    asyncio.run(main())
