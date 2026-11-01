# 三工具 Function Calling：检索封装实施计划

**执行方式：** 沿用已确认的教学方式，由学习者逐步编写，导师检查源码并进行必要的离线验收。本计划只覆盖一个可独立检查的检索函数，不一次性交付完整 Agent 应用。

**Goal:** 在 app/usage_tools.py 中实现 search_tool_docs，复用现有 Embedding 和按工具过滤的 Qdrant 查询，返回原始片段列表。

**Architecture:** 函数先异步向量化问题，再通过 asyncio.to_thread 调用同步检索。模型参数解析、严格校验及 ok/data/error 包装属于后续分发层；本步函数接受后续分发层校验后的输入。

**Tech Stack:** Python、asyncio、现有 Embedding 客户端、Qdrant 检索模块。

**设计依据：** [Function Calling 设计](../specs/2026-10-30-tool-docs-function-calling-design.md)。学习者已确认工具负责返回片段、最终回答由模型生成。

## 文件与职责

- 新建文件：./app/usage_tools.py。
- 复用 [Embedding 函数](../../../app/embedding_client.py) 与 [检索函数](../../../app/tool_retrieval.py)。
- 现有 app/tools.py、tool_call_demo.py 和 /tools/ask 保留作已有流程及后续对照。

## 任务 1：编写封装函数

- [x] 学习者创建文件，写入以下本步代码。

```python
import asyncio

from app.embedding_client import embed_text
from app.tool_retrieval import search_tool_chunks


async def search_tool_docs(question: str, tool_name: str) -> list[dict]:
    query_vector = await embed_text(question)
    chunks = await asyncio.to_thread(
        search_tool_chunks, query_vector, tool_name
    )
    return chunks
```

## 任务 2：仅检查导入

- [x] 学习者在项目目录执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from app.usage_tools import search_tool_docs; print('导入成功')"
```

预期打印“导入成功”。导入本步模块不调用函数，尚不请求 Embedding 或查询数据库。

## 任务 3：导师检查数据传递

- [x] 读取函数源码，核对参数顺序、两个 await 和返回值。
- [x] 用模拟 Embedding 与检索依赖进行以下离线实验，确认返回片段内容和元数据完整保留；同时核对同步查询交给了 to_thread。

以下片段在项目目录的 .venv Python 中运行，使用模拟依赖，不访问真实模型和数据库：

```python
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import app.usage_tools as usage_tools


async def verify():
    vector = [0.1] * 2048
    chunks = [{
        "chunk_id": "offline-001",
        "tool_name": "getinfo",
        "source": "offline.md",
        "section": "offline",
        "source_type": "tool_manual",
        "content": "Offline check only.",
    }]
    embedding = AsyncMock(return_value=vector)
    retrieval = Mock()
    thread_call = AsyncMock(return_value=chunks)

    with patch.object(usage_tools, "embed_text", embedding), \
         patch.object(usage_tools, "search_tool_chunks", retrieval), \
         patch.object(usage_tools.asyncio, "to_thread", thread_call):
        result = await usage_tools.search_tool_docs("offline question", "getinfo")

    embedding.assert_awaited_once_with("offline question")
    thread_call.assert_awaited_once_with(retrieval, vector, "getinfo")
    assert result is chunks
    assert result[0]["chunk_id"] == "offline-001"
    print("PASS: original chunks returned with metadata; retrieval runs through to_thread.")


asyncio.run(verify())
```

## 本步完成条件与下一步

函数可导入，输入问题用于 Embedding，得到的向量和 tool_name 一起传给现有检索函数，返回值是原始片段列表。本步不需要真实模型调用来验证数据传递。

完成后进入工具定义与分发：添加 SEARCH_TOOL_DOCS_TOOL，复用 ToolRagRequest 严格校验模型参数，并生成 ok/data/error 工具结果。该分发层的实施步骤将在本步验收后单独细化；模型调用循环与新接口继续按设计顺序推进。

## 自审记录

- [x] 范围只含检索封装，工具声明、分发、模型循环和接口未计为本步完成。
- [x] 复用函数均已在当前代码中核对，本步新增函数在计划内有完整定义。
- [x] 导入命令和离线实验均不调用真实模型；输入输出与设计中的职责划分一致。

2026-10-30 验收：学习者反馈导入成功，导师读取源码并完成正常片段及空列表两种模拟回放。问题原样传入 Embedding，得到的向量与 tool_name 正确交给 to_thread，原始列表及其元数据保持不变。没有调用真实模型或数据库，本步完成。
