# 三工具 Function Calling：有界循环与累计引用计划

**执行方式：** 学习者复用旧巡检演示中的有界循环思路，调整当前 main 的请求部分；导师先离线检查再核对实际实现。本步仅做导入与模拟验收。

**Goal:** 支持至多两次顺序工具执行，以最多三次文本模型请求生成最终回答，引用允许来自本任务任一成功检索。

**Architecture:** 保留 main 的 messages 初始化和 run_with_timeout，将两个客户端上下文合并为一个，在上下文内循环。无工具调用时统一校验并返回；有工具调用时分发、累计 ID、追加 assistant/tool 消息后进入下一轮。每轮最多一个调用，第三次文本请求设为 none 并在程序侧拒绝其工具请求。现有 90 秒包装覆盖整个循环。

**Tech Stack:** Python、AsyncArk、asyncio、现有工具分发与 validate_usage_answer。

**修改文件：** ./usage_agent_demo.py。

## 任务 1：设置请求上限

- [x] 在 TASK_TIMEOUT_SECONDS 后添加：

```python
MAX_TOOL_CALLS = 2
MAX_MODEL_REQUESTS = MAX_TOOL_CALLS + 1
```

上限是最多两次工具执行，而不是要求每题都执行两次。模型可在第一或第二次请求直接返回符合规则的最终回答。

## 任务 2：允许按需查询多类资料

- [x] 在现有 system content 相邻字符串内追加：

```python
                "需要多类工具资料时分轮检索，最终回答可综合本次任务中所有成功检索的片段。"
```

不修改工具名、参数 schema、Top-4 或资料不足规则。

## 任务 3：替换模型请求部分

- [x] 保留 main 前面的 messages 初始化；从第一个 async with AsyncArk.volc 开始，一直到 main 末尾 return result 的旧请求代码整段替换为以下内容。run_with_timeout 顶层函数保留在 main 外。

```python
    allowed_ids: set[str] = set()
    async with AsyncArk.volc(
        api_key=os.environ["ARK_API_KEY"],
        timeout=60.0,
        max_retries=0,
    ) as client:
        for request_index in range(MAX_MODEL_REQUESTS):
            is_last_request = request_index == MAX_MODEL_REQUESTS - 1
            tool_choice = "none" if is_last_request else "auto"
            print(f"文本模型请求 {request_index + 1}/{MAX_MODEL_REQUESTS}, tool_choice={tool_choice}")
            completion = await client.chat.completions.create(
                model=os.environ["ARK_MODEL"],
                messages=messages,
                tools=[SEARCH_TOOL_DOCS_TOOL],
                tool_choice=tool_choice,
            )
            message = completion.choices[0].message
            print("普通文本：", message.content)
            print("工具请求：", message.tool_calls)

            if not message.tool_calls:
                result = validate_usage_answer(message.content, allowed_ids)
                print("最终回答：")
                print(result.model_dump_json(indent=2))
                return result
            if len(message.tool_calls) != 1:
                raise ValueError("本练习每轮只执行一个工具调用")
            if is_last_request:
                raise RuntimeError("已达到工具调用上限，停止执行工具")

            tool_call = message.tool_calls[0]
            tool_result = await execute_usage_tool(
                tool_call.function.name,
                tool_call.function.arguments,
            )
            if tool_result["ok"]:
                allowed_ids.update(
                    chunk["chunk_id"] for chunk in tool_result["data"]
                )
            print("工具执行结果：")
            print(json.dumps(tool_result, ensure_ascii=False, indent=2))
            messages.append(message.model_dump(mode="json", exclude_none=True))
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })
            print("消息顺序：", [item["role"] for item in messages])

    raise RuntimeError("模型在请求上限内未生成最终回答")
```

引用集合在循环之前初始化，每个成功结果使用 update 追加；不能每轮重新赋值，否则第二轮会丢失第一轮的证据 ID。失败结果不作为文档证据。集合累计不构成长期记忆，它仅服务本次 main 调用的校验。

第三次请求使用 none 是正常收尾控制；即使服务仍返回工具请求，程序也必须先拦截，不能执行第三次工具。最多两个执行由一轮一个工具、最后一轮禁止工具共同保证。

## 任务 4：离线验收

- [x] 导师预检查计划代码：无工具直接澄清、一工具后回答、两工具累计引用、第三次继续工具请求、同轮多个工具、错误后修正参数等模拟场景。
- [x] 学习者完成修改；导师已实际导入源码并进行离线检查。手工复查命令如下：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from usage_agent_demo import main, run_with_timeout; print('导入成功')"
```

- [x] 导师核对实际代码：最多三次文本请求、两次工具执行、第三轮 none、单客户端生命周期、每次 tool_call_id 对应、跨轮引用可用且未知 ID 拦截。模拟结果不写入正式评测目录。

## 完成边界

本步在当前命令行 main 中实现有界流程，仍由 run_with_timeout 提供共享预算。后续再将业务执行入口抽入 app/usage_agent.py，并将命令行缩为调用入口，然后接仅收 question 的 FastAPI 接口。多轮工具流程不等同于已完成复杂任务规划或长期记忆。

## 导师预检查记录（2026-11-01）

将计划中的常量、提示词追加和循环代码与当前源码在内存中组合，用模拟 SDK 消息和工具结果执行七个场景：首轮直接澄清、一次工具后回答、两次成功检索后同时引用两轮资料、第三轮仍要求工具、同轮多个调用、参数错误后修正、最终未知引用。结果符合预期：最多三次文本请求和两次工具执行；第三轮设 none 且程序拒绝额外执行；只有成功结果累计进引用集合；一/两次工具的最终回答均返回 RagAnswer。单个客户端在成功和异常时都关闭，每个回传工具结果均与原调用 ID 匹配。

预检查不修改学习者源码，不请求真实模型、Embedding 或数据库，不向正式评测目录写模拟结果。实际循环实现及调用预算仍待学习者编写后核对。

## 实际实现验收（2026-11-01）

学习者反馈已写完，导师读取并导入当前 usage_agent_demo.py。通过真实 run_with_timeout 调用真实 main，替换 SDK 客户端与工具分发器，执行七种模拟场景：首轮澄清、一次工具后回答、两次成功工具累计引用、第三轮仍请求工具、同轮多个调用、参数错误后修正、未知引用。均符合预期：至多三次请求与两次执行，第三次设 none，第一轮资料在第二轮后仍可引用；超额与同轮多调用先拦截，成功/异常均关闭同一客户端，工具回传 ID 匹配。

本步有界循环和累计引用的代码验收完成。没有真实模型、Embedding 或数据库调用，没有修改应用源码或写入正式评测结果。下一步进行跨工具的真实问题回放，检验模型是否按需求依次获取两类资料；模拟通过不计为真实模型已完成该行为。
