from pathlib import Path
import json
import asyncio
import os
from arkruntime import AsyncArk
from app.embedding_client import embed_text
PROJECT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = PROJECT_DIR /"data"/"docs"/"kernel_check.json"

async def main():
    with open(FIXTURES_DIR,"r",encoding = "utf-8")as file:
        res = json.load(file)
    vector = await embed_text(res["content"])
    print(type(vector))
    print("向量维度：",len(vector))
    print("前5个数：",vector[:5])

if __name__ == "__main__":
    asyncio.run(main())
