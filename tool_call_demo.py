import os
from arkruntime import AsyncArk
import asyncio
import json
from app.tools import GET_CHECK_RECORD_TOOL, SEARCH_SOP_TOOL, execute_tool
TASK_TIMEOUT_SECONDS = 90.0
MAX_TOOL_CALLS = 2
MAX_MODEL_REQUESTS = MAX_TOOL_CALLS + 1
async def main(question:str):
    messages=[
    {
        "role":"system",
        "content":"你是巡检助手。查询指定巡检记录时,先调用工具获取记录，不得编造记录内容。工具返回 ok=false 时，根据 error.code 和 error.message 说明失败原因，区分参数错误与记录不存在，不编造记录内容。查询检查方法、复核步骤或验收要求时，先调用 search_sop。仅依据返回片段回答，缺少依据时明确说明。每轮最多请求一个工具。需要结合记录与 SOP 时，先查记录，再根据记录中的检查项检索 SOP，最后结合两者回答。区分实际值、配置期望值和文档规定:缺少依据时明确说明。严格区分巡检执行状态与业务检查结果：check_status 中，completed 表示巡检执行完成，failed 表示巡检执行失败，不得仅凭 failed 判断服务器不达标。overall_result 中，pass 表示本次基线检查通过，fail 表示已有检查结果不符合配置基线，error 表示本次检查存在执行或采集错误，无法形成完整的达标判断。部分数据缺失时，保留已经获得的检查结果，明确哪些项目无法判断，不得把缺失值当作 0 或配置期望值。"
    },
    {
        "role":"user",
        "content":question,
    },
]
    async with AsyncArk.volc(
        api_key=os.environ["ARK_API_KEY"],
        timeout=60.0,
        max_retries=0,
    )as client:
        for request_index in range(MAX_MODEL_REQUESTS):
            is_last_request = request_index ==MAX_MODEL_REQUESTS-1
            tool_choice = "none" if is_last_request else "auto"
            print(
                f"文本模型请求 {request_index + 1}/{MAX_MODEL_REQUESTS}, "
                f"tool_choice={tool_choice}"
            )
            completion = await client.chat.completions.create(
                model=os.environ["ARK_MODEL"],
                messages = messages,
                tools=[GET_CHECK_RECORD_TOOL,SEARCH_SOP_TOOL],
                tool_choice=tool_choice,
            )
            message = completion.choices[0].message
            print("普通文本：", message.content)
            print("工具请求：", message.tool_calls)
            if not message.tool_calls:
                print("最终回答:", message.content)
                return message.content
            if len(message.tool_calls)>1:
                raise ValueError("本练习每轮最多一个工具调用")
            if is_last_request:
                raise RuntimeError("已达到工具调用上限,停止执行工具")
            tool_call = message.tool_calls[0]
            tool_result = await execute_tool(
                tool_call.function.name,
                tool_call.function.arguments,
            )
            print(json.dumps(tool_result,ensure_ascii=False,indent = 2))
            messages.append(
                message.model_dump(mode="json", exclude_none=True)
            )

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })
            print("消息顺序：", [item["role"] for item in messages])
async def run_with_timeout(question:str):
    try:
        async with asyncio.timeout(TASK_TIMEOUT_SECONDS):
            return await main(question)
    except TimeoutError:
        print("任务超时")
        raise
if __name__ == "__main__":
    demo_question = "请查询巡检记录1004,说明实际GPU数量是否已采集。"
    asyncio.run(run_with_timeout(demo_question))
