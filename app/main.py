from fastapi import FastAPI,HTTPException
from app.schemas import AnalysRequest,AnalysResult,RagRequest,RagAnswer
from app.records import load_record
import asyncio
from pydantic import ValidationError
from app.model_client import analyze_record
from arkruntime._exceptions import ArkAPIError, ArkAPITimeoutError
from app.embedding_client import embed_text
from app.retrieval import search_chunks
from app.rag_client import answer_question
from app.schemas import ToolRagRequest
from app.tool_retrieval import search_tool_chunks
from app.tool_rag_client import answer_question as answer_tool_question
from app.schemas import AgentRequest
from app.usage_agent import run_usage_agent
MODEL_TIMEOUT_SECONDS = 30.0
RAG_TIMEOUT_SECONDS = 60.0
app = FastAPI()
@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/analyze",response_model=AnalysResult)
async def analyze(request:AnalysRequest):
    try:
        record = await asyncio.to_thread(load_record, request.record_id)
        async with asyncio.timeout(MODEL_TIMEOUT_SECONDS):
            text = await analyze_record(record)
        result = AnalysResult.model_validate_json(text)
    except (TimeoutError, ArkAPITimeoutError):
        raise HTTPException(status_code=504, detail="模型调用超时")

    except ArkAPIError:
        raise HTTPException(status_code=502, detail="模型服务调用失败")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="巡检记录不存在")

    except ValidationError:
        raise HTTPException(status_code=502, detail="模型输出格式不符合约定")
    return result


@app.post("/ask", response_model=RagAnswer)
async def ask(request: RagRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422,detail="问题不能为空")
    try:
        async with asyncio.timeout(RAG_TIMEOUT_SECONDS):
            query_vector = await embed_text(question)
            chunks = await asyncio.to_thread(search_chunks,query_vector,request.platform)
            if not chunks:
                return RagAnswer(
                    answer="当前知识库未检索到可用资料。",
                    evidence_status="insufficient",
                    citations=[],
                )
            try:
                result = await answer_question(question,chunks)
            except (ValidationError,ValueError):
                    raise HTTPException(status_code=502, detail="模型输出格式不符合约定")
    except (TimeoutError, ArkAPITimeoutError):
        raise HTTPException(status_code=504, detail="模型调用超时")

    except ArkAPIError:
        raise HTTPException(status_code=502, detail="模型服务调用失败")
    return result

@app.post("/tools/ask", response_model=RagAnswer)
async def ask_tool(request: ToolRagRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422,detail="问题不能为空")
    stage = "embedding"
    try:
        async with asyncio.timeout(RAG_TIMEOUT_SECONDS):
            query_vector = await embed_text(question)
            stage = "retrieval"
            chunks = await asyncio.to_thread(search_tool_chunks,query_vector,request.tool_name)
            if not chunks:
                return RagAnswer(
                    answer="当前知识库未检索到可用资料。",
                    evidence_status="insufficient",
                    citations=[],
                )
            try:
                stage = "generation"
                result = await answer_tool_question(question,chunks)
            except (ValidationError,ValueError):
                    raise HTTPException(status_code=502, detail="模型输出格式不符合约定")
    except (TimeoutError, ArkAPITimeoutError):
        print("RAG超时阶段:",stage,flush=True)
        raise HTTPException(status_code=504, detail="模型调用超时")

    except ArkAPIError:
        raise HTTPException(status_code=502, detail="模型服务调用失败")
    return result

@app.post("/agent/ask", response_model=RagAnswer)
async def ask_agent(request: AgentRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="问题不能为空")
    try:
        return await run_usage_agent(question)
    except (TimeoutError, ArkAPITimeoutError):
        raise HTTPException(status_code=504, detail="Agent处理超时")
    except ArkAPIError:
        raise HTTPException(status_code=502, detail="模型服务调用失败")
    except (ValidationError, ValueError, RuntimeError):
        raise HTTPException(status_code=502, detail="Agent未能完成本次处理")
