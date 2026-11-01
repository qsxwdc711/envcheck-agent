import json
import os
from arkruntime import AsyncArk
from app.schemas import RagAnswer

SYSTEM_PROMPT = "1.你是巡检文档小助手，主要负责回答一些怎么检查的问题，输入包含问题和检索片段,2.依据提供的检索片段，区分检查方法，实际检查结果和验收标准,3.只引用本次提供、且实际支持回答内容的chunk_id，无关片段不列入引用,4.只返回一个json对象，不加markdown围栏或前后说明，包含下面三个字段： answer：字符串，依据片段回答本题，或说明缺少的依据。evidence_status：字符串，只能是 sufficient 或 insufficient，根据本题资料是否充分确定。citations：字符串列表，只列本次输入中实际支持回答内容的 chunk_id。.5.先判断片段是否包含回答本题所需的明确依据。依据足够时，evidence_status 返回 sufficient；缺少本题所需的结果、标准或根因证据时，返回 insufficient，并在 answer 中说明缺少什么依据。不得从检查命令、空白结果、相似度分数或常识中补出具体版本、基线或根因"

async def answer_question(question:str,chunks:list[dict])->RagAnswer:
    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        {
            "role":"user",
            "content":json.dumps(
                {"question":question,"chunks":chunks},
                ensure_ascii=False,
            ),
        },
    ]
    async with AsyncArk.volc(
        api_key=os.environ["ARK_API_KEY"],
        timeout=60.0,
        max_retries=0,
    )as client:
        completion = await client.chat.completions.create(
            model=os.environ["ARK_MODEL"],
            messages=messages,
        )
        result = RagAnswer.model_validate_json(
            completion.choices[0].message.content
        )
        allowed_ids = {chunk["chunk_id"] for chunk in chunks}
        if not set(result.citations).issubset(allowed_ids):
            raise ValueError("回答引用了本次检索之外的片段")
        if result.evidence_status=="sufficient"and not result.citations:
            raise ValueError("资料充足的回答必须提供至少一个引用")
    return result
