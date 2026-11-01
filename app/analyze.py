import os
import json
from app.schemas import RagAnswer
from arkruntime import AsyncArk
def build_analysis_context(record:dict,question:str,chunks:list[dict]):
    dict1 = {"question":question,"record":record,"chunks":chunks}
    return dict1

INSPECTION_SYSTEM_PROMPT="角色与任务：你是算力服务器巡检分析助手，根据巡检记录和检索文档回答问题，解释差异并给出有依据的复核方法。配置与标准：record 中的期望值表示当前配置基线；没有文档支持时，不得将其描述为 SOP 明确规定，也不得编造版本差异的根因。输出类型：answer 是字符串；evidence_status 只能是 sufficient 或 insufficient；citations 是字符串列表。1.输入中的question表示传入的用户问题，record表示完整的原始巡检记录，chunks表示传入的检索片段列表2.区分采集到的实际值、配置期望值、文档检查方法和验收标准。3.先识别 question 中明确要求回答的事项。若本题各项均能由 record 或 chunks 提供依据，evidence_status 返回 sufficient。只有缺少回答其中某项所必需的依据时，才返回 insufficient，并说明缺少什么。未被询问的根因或验收标准缺失，不影响本题的充分性判断；不得把回答中自行扩展的事项作为判定资料不足的理由4.citations 只填写本次 chunks 中实际支持文档陈述的 chunk_id，不要为巡检记录伪造文档引用。只返回一个包含 answer、evidence_status、citations 三个字段的 JSON 对象，不添加 Markdown 围栏或前后说明"

async def answer_inspection(context:dict)->RagAnswer:
    messages = [
        {"role":"system","content":INSPECTION_SYSTEM_PROMPT},
        {
            "role":"user",
            "content":json.dumps(context,ensure_ascii=False),
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
        allowed_ids = {chunk["chunk_id"] for chunk in context["chunks"]}
        if not set(result.citations).issubset(allowed_ids):
            raise ValueError("回答引用了本次检索之外的片段")
    return result
