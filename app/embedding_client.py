import os
from arkruntime import AsyncArk
async def embed_text(text:str):
    async with AsyncArk.volc(
        api_key=os.environ["ARK_API_KEY"],
        timeout=60.0,
        max_retries=0,
    )as client:
        response = await client.multimodal_embeddings.create(
            model = os.environ["ARK_EMBEDDING_MODEL"],
            input=[{"type": "text", "text": text}],
            encoding_format="float",
        )
        print("实际模型：", response.model)
        vector = response.data.embedding
        return vector
