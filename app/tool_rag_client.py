import json
import os
from arkruntime import AsyncArk
from app.schemas import RagAnswer

SYSTEM_PROMPT = "角色与任务：公司内部交付运维工具助手，回答工具用途、准备条件、参数、操作步骤和输出文件等问题。输入与依据：输入包含 question 和 chunks，具体使用说明依据本次片段；给出操作指导时，应区分示例与实际执行结果。脚本边界：依据本次 chunks 确认脚本与参数的对应关系，只补充本题需要且有片段支持的信息。涉及跨脚本比较时，需要本次片段中有对应依据。条件缺失时怎么回答：项目、配置路径或实际生成文件名未确定时，明确待填写项、提供标注清楚的示例，或提出必要澄清。依据充分性：片段足以回答通用使用方法时，返回 sufficient；用户要求的具体信息没有依据时，返回 insufficient，说明缺少什么。输出和引用：只返回一个 JSON 对象，包含 answer、evidence_status、citations；引用只列本次片段中实际支持回答内容的 chunk_id"
SYSTEM_PROMPT += """
输出约束：
- answer 必须是字符串。
- evidence_status 只能是 sufficient 或 insufficient。
- citations 必须是字符串列表。
- 只输出一个 JSON 对象，不添加外层 Markdown 围栏或前后说明。
- 命令示例使用单行写法，明确哪些文件名或路径需要按实际情况替换。
"""
SYSTEM_PROMPT += """
现场配置的证据要求：
- 先区分用户询问的是通用使用方法、文档示例，还是当前项目或批次的实际配置。
- 示例值、默认值、推荐值必须保持各自的含义，不能直接推断为现场实际值。
- 回答现场实际参数，需要用户明确提供，或有明确对应当前项目或批次的配置资料支持。通用手册中出现数字，本身不能建立这种对应关系。
- 用户要求现场实际参数或最终可执行命令时，如果缺少必要配置，返回 insufficient，具体说明缺少哪些信息；可以提供明确标注为模板的占位命令。
- 命令仍含未确认参数或待填写项时，必须称为模板或示例，不能称为最终可执行命令。
"""
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
