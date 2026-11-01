# 三工具 Function Calling：执行工具和消息回填实施计划

**执行方式：** 沿用已确认的导师讲解、学习者手写、离线核对与真实回放方式。本步只增加工具执行与消息回填。

**Goal:** 使用首轮模型返回的 name 与 arguments 执行检索，将原 assistant 请求与对应 tool 结果依次加入 messages。

**Architecture:** 复用 app/usage_tools.py 中已验收的 execute_usage_tool；严格参数校验、Embedding 与本地检索均由该函数及其依赖负责。消息中的 tool_call_id 对应本次请求 ID，工具返回字典序列化为 JSON 字符串写入 content。本步仍只有一次文本模型请求，最终模型生成留至下一步。

**Tech Stack:** Python、asyncio、json、火山方舟工具消息、现有工具分发器。

**修改文件：** ./usage_agent_demo.py。

## 任务 1：补充导入

- [x] 增加 json，扩展工具导入：

```python
import json
from app.usage_tools import SEARCH_TOOL_DOCS_TOOL, execute_usage_tool
```

## 任务 2：执行并回填消息

- [x] 将以下代码放在 main 内、打印工具请求之后，整体缩进四个空格：

```python
    if not message.tool_calls:
        print("本轮没有工具调用：", message.content)
        return
    if len(message.tool_calls) != 1:
        raise ValueError("本练习每轮只执行一个工具调用")

    tool_call = message.tool_calls[0]
    tool_result = await execute_usage_tool(
        tool_call.function.name,
        tool_call.function.arguments,
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
```

当前代码接在 AsyncArk 上下文之后仍有效：首轮文本客户端已经关闭，Embedding 封装会自行管理其客户端。本步不添加第二次文本模型请求；下一步需将最终请求置于可用客户端上下文内。

## 任务 3：核对与运行

- [x] 导师使用模拟工具结果核对追加片段：消息顺序正确、ID 匹配、JSON 内容保持返回结构、无调用与多调用分支均不执行检索。
- [x] 学习者运行一次真实请求：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\usage_agent_demo.py
```

预期：模型选择 getinfo；工具结果为 ok=true、data 为检索原始片段、error=null；消息顺序为 system、user、assistant、tool。当前数据正常命中时返回至多三个 getinfo 片段，至少应检查 Word 用法相关片段是否在其中。空结果仍是成功执行；错误结果按实际 code 核对，不通过编造资料补全。

- [x] 导师读取学习者实际实现与输出，区分首轮工具请求、工具执行结果和最终模型回答。

此轮正常路径包含一次文本模型请求、一次 Embedding 请求和一次本地向量检索。真实外部调用由学习者运行，导师离线检查使用模拟结果，不写入正式向量库。

## 完成边界

完成后可证明 Python 执行检索并准备了正确的对话消息。此时工具结果尚未发送到下一轮文本模型；后续加入最终 JSON 生成、结构与引用校验、有界循环以及只接收问题的接口。

## 导师预检查记录（2026-10-31）

从本计划提取追加代码，用已安装 SDK 的 ChatCompletionMessage 构造请求，替换分发器为模拟依赖，确认参数转交、四条消息顺序、原 assistant 请求保留、tool_call_id 匹配和工具 JSON 往返一致；无工具调用和多个工具调用均不执行检索。本项验证的是拟追加片段，学习者实际源码修改及真实工具执行输出仍待验收。未由导师调用模型或数据库，也未修改学习者应用源码。

## 实际实现与真实回放验收（2026-10-31）

学习者真实输出包含一个 search_tool_docs 请求，id=call_dil7fax8sv58va7b8v49gehi，资料范围为 getinfo。Embedding 返回实际模型 doubao-embedding-vision-250615；工具结果为 ok=true、error=null，原始片段依次为 getinfo-usage-006、002、001，其中 006 提供 Word 报告生成脚本、参数与输出位置。消息顺序为 system、user、assistant、tool。该输出证明工具已执行并准备了对话消息，尚未产生最终模型回答。

导师读取实际 usage_agent_demo.py，并使用模拟客户端和分发器执行其 main：一次模型请求、工具名及原始参数转交、原 assistant 请求保留、匹配的 tool_call_id、工具结果 JSON 往返均通过。无工具请求与多个请求的分支均不执行分发。离线核对没有真实模型、Embedding 或数据库调用。
