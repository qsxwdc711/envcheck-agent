import asyncio

from app.embedding_client import embed_text
from app.tool_retrieval import search_tool_chunks
from app.schemas import ToolRagRequest
import json
SEARCH_TOOL_DOCS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_tool_docs",
        "description": (
            "检索内部交付运维工具使用文档，返回相关片段。"
            "采集服务器信息、生成报告选择 getinfo；"
            "IB/RoCE 线序检查选择 nic_link_check；"
            "资源下载、镜像制作与验证选择 aidoc_download。"
        ),
        "parameters": ToolRagRequest.model_json_schema(),
    },
}
async def search_tool_docs(question: str, tool_name: str) -> list[dict]:
    query_vector = await embed_text(question)
    chunks = await asyncio.to_thread(
        search_tool_chunks,
        query_vector,
        tool_name,
        limit=4,
    )
    return chunks

async def execute_usage_tool(function_name: str, arguments_text: str) -> dict:
    if function_name != "search_tool_docs":
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "UNSUPPORTED_TOOL",
                "message": "不支持的工具名称。",
            },
        }

    try:
        arguments = json.loads(arguments_text)
        params = ToolRagRequest.model_validate(
            arguments, strict=True, extra="forbid"
        )
        question = params.question.strip()
        if not question:
            raise ValueError("问题不能为空")
    except (ValueError, TypeError):
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "请提供非空 question 和合法 tool_name，且不要添加额外字段。",
            },
        }

    chunks = await search_tool_docs(question, params.tool_name)
    return {"ok": True, "data": chunks, "error": None}
