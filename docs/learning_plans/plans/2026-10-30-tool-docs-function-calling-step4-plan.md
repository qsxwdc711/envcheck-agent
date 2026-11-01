# 三工具 Function Calling：首次模型工具选择实施计划

**执行方式：** 学习者编写首轮模型请求并运行，导师核对代码及真实输出。本步先观察调用请求，下一步再执行工具并将结果回传。

**Goal:** 让模型根据自然语言问题生成 search_tool_docs 调用请求，并选择正确的 tool_name。

**Architecture:** 复用旧演示的 AsyncArk 调用格式，将已验收的 SEARCH_TOOL_DOCS_TOOL 放入 tools。用户问题不提供工具名，由模型从工具说明和参数 schema 推断资料分类。本步只打印首轮 message，不执行模型请求的工具。

**Tech Stack:** Python、asyncio、火山方舟原生工具调用、已实现的检索工具声明。

**新建文件：** ./usage_agent_demo.py。导师于本步计划前确认文件尚不存在。

## 任务 1：编写首轮请求

- [x] 学习者写入以下代码。

```python
import asyncio
import os

from arkruntime import AsyncArk
from app.usage_tools import SEARCH_TOOL_DOCS_TOOL


async def main(question: str):
    messages = [
        {
            "role": "system",
            "content": (
                "你是内部交付运维工具助手。"
                "回答工具使用问题前，先调用 search_tool_docs 查询文档。"
                "根据用户需求选择 tool_name，每轮最多请求一个工具。"
                "需求不明确、无法判断资料范围时，先澄清。"
            ),
        },
        {"role": "user", "content": question},
    ]

    async with AsyncArk.volc(
        api_key=os.environ["ARK_API_KEY"],
        timeout=60.0,
        max_retries=0,
    ) as client:
        completion = await client.chat.completions.create(
            model=os.environ["ARK_MODEL"],
            messages=messages,
            tools=[SEARCH_TOOL_DOCS_TOOL],
            tool_choice="auto",
        )

    message = completion.choices[0].message
    print("普通文本：", message.content)
    print("工具请求：", message.tool_calls)


if __name__ == "__main__":
    question = "我已经采集得到一个 SOP JSON 文件，想把它生成 Word 报告，应该怎么做？"
    asyncio.run(main(question))
```

单次 SDK 超时仍为 60 秒且不重试；完整调用循环、任务总预算、最终回答校验属于后续步骤。此脚本当前只发起一次文本模型请求，不调用 Embedding 或执行本地检索。

## 任务 2：学习者执行一次真实请求

- [x] 在模型环境变量已配置的项目终端执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\usage_agent_demo.py
```

预期工具请求包含 function.name=search_tool_docs；function.arguments 为 JSON 字符串，解析后包含非空 question 与 tool_name=getinfo。检索问题可由模型改写，不要求字面等于用户原句。普通文本可能为空，主要核对 tool_calls。

## 任务 3：导师核对

- [x] 核对脚本中的 messages、tools、tool_choice 和模型读取方式。
- [x] 读取真实输出，确认每轮仅一个工具请求、函数名正确、参数符合既有模型、分类与需求相符。
- [x] 记录本次为首轮工具选择证据；不将打印调用请求描述为工具已执行或最终回答已生成。

## 完成条件与后续

用户没有提供工具名，模型正确生成 getinfo 分类的检索请求。随后添加 execute_usage_tool 调用，并将原 assistant 工具请求及对应 tool 消息加入 messages，再请求最终 JSON。调用次数上限、总预算与引用校验在完整循环步骤中加入。

## 自审记录

- [x] 新脚本使用已存在且已验收的工具声明，SDK 结构与旧演示一致。
- [x] 本步范围为首轮请求，未将工具执行和最终回答计为完成。
- [x] 执行命令只发起一次文本模型请求，实际调用由学习者操作。

## 验收记录（2026-10-31）

学习者提供的首轮真实结果：普通文本为空；一个工具请求，id 为 call_t0dcfah62btb0ggvr00efb2i，function.name 为 search_tool_docs，arguments 为 {"question": "已采集 SOP JSON 文件，如何生成 Word 报告", "tool_name": "getinfo"}。用户原问题没有指定工具名，模型选择的资料范围符合 Word 报告需求。

导师读取当前 usage_agent_demo.py，离线确认语法、一次 create 请求、工具声明与 auto 选择配置；返回参数的类型和取值符合现有 ToolRagRequest。未由导师请求模型、Embedding 或数据库。本步只确认调用请求，下一步执行工具并回填消息。
