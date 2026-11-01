import asyncio
from app.embedding_client import embed_text
from app.retrieval import search_chunks
import json
from pydantic import ValidationError
from app.schemas import AnalysRequest, RagRequest
from app.records import load_record
GET_CHECK_RECORD_TOOL = {
    "type":"function",
    "function":{
        "name":"get_check_record",
        "description":"根据用户提供的编号，查询一条已有的巡检记录。例如“分析记录 1001 为什么没通过”时，需要先查询它",
        "parameters":{
            "type":"object",
            "properties":{
                "record_id": {
                    "type": "integer",
                    "description": "需要查询的巡检记录编号"
}
            },
            "required":["record_id"],
        },
    },
}

SEARCH_SOP_TOOL = {
    "type":"function",
    "function":{
        "name":"search_sop",
        "description":"用于检索sop中的检查方法、复核步骤和验收要求,返回相关文档片段。",
        "parameters":{
            "type":"object",
            "properties":{
                "question":{
                    "type":"string",
                    "description":"需要查询的自然语言问题，例如怎么查看 GPU 驱动版本？"
                },
                "platform":{
                    "type":"string",
                    "description":"文档适用平台,例如nvidia",
                },
            },
            "required":["question","platform"],
        }
    }
}

async def search_sop(question: str, platform: str) -> list[dict]:
    query_vector = await embed_text(question)
    chunks = await asyncio.to_thread(search_chunks,query_vector,platform)
    return chunks

async def execute_tool(tool_name: str, arguments_text: str) -> dict:
    if tool_name not in {"get_check_record","search_sop"}:
        raise ValueError("不支持的工具名称")
    try:
        arguments = json.loads(arguments_text)
        if tool_name == "get_check_record":
            params = AnalysRequest.model_validate(
                arguments,strict=True,extra="forbid"
            )
        else:
            params = RagRequest.model_validate(
                arguments,strict=True,extra="forbid"
            )
    except(json.JSONDecodeError,ValidationError):
        tool_result={
            "ok":False,
            "data":None,
            "error":{
                "code":"INVALID_ARGUMENTS",
                "message":"工具参数无效，请按对应工具要求提供字段和正确类型。"
            }
        }
    else:
        if tool_name == "get_check_record":
            try:
                record = await asyncio.to_thread(load_record,params.record_id)
                tool_result={
                    "ok":True,
                    "data":record,
                    "error":None,
                }
            except FileNotFoundError:
                tool_result = {
                    "ok":False,
                    "data": None,
                    "error": {
                        "code": "RECORD_NOT_FOUND",
                        "message": f"未找到巡检记录{params.record_id}",
                    },
                }
            except json.JSONDecodeError:
                tool_result = {
                    "ok":False,
                    "data":None,
                    "error":{
                        "code":"RECORD_DATA_INVALID",
                        "message":f"巡检记录{params.record_id}的内容不是合法 JSON,无法读取。",
                    },
                }
        else:
            chunks = await search_sop(
                params.question,params.platform
            )
            tool_result = {
                "ok":True,"data":chunks,"error":None
            }
    return tool_result
