# 三工具 Function Calling：参数校验与分发实施计划

**执行方式：** 学习者编写一个分发函数，导师离线验证输入错误拦截与成功结果包装；模型调用循环仍在后续步骤实现。

**Goal:** 在 app/usage_tools.py 中实现 execute_usage_tool，将模型返回的函数名及 JSON 参数字符串转换为受校验的检索调用。

**Architecture:** 先检查允许调用的函数名，再解析参数 JSON，使用 ToolRagRequest 严格检查字段、类型与枚举，并排除空白问题。通过后调用 search_tool_docs，返回 ok/data/error。检索服务异常由后续上层循环处理，参数检查的 try 不包含检索执行。

**Tech Stack:** Python、json、Pydantic、asyncio、现有检索封装。

**文件：** ./app/usage_tools.py。

## 任务 1：导入 JSON 模块

- [x] 在导入部分增加：

```python
import json
```

现有 ToolRagRequest 导入继续复用。当前安装版本中 JSONDecodeError 和 Pydantic ValidationError 都继承 ValueError，导师已离线核对；TypeError 用于 JSON 输入不是可解析类型等情况。

## 任务 2：添加分发函数

- [x] 在 search_tool_docs 之后添加：

```python
async def execute_usage_tool(function_name: str, arguments_text: str) -> dict:
    if function_name != "search_tool_docs":
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "UNSUPPORTED_TOOL",
                "message": "不支持的工具名称。",
            },
        }

    try:
        arguments = json.loads(arguments_text)
        params = ToolRagRequest.model_validate(
            arguments, strict=True, extra="forbid"
        )
        question = params.question.strip()
        if not question:
            raise ValueError("问题不能为空")
    except (ValueError, TypeError):
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "请提供非空 question 和合法 tool_name，且不要添加额外字段。",
            },
        }

    chunks = await search_tool_docs(question, params.tool_name)
    return {"ok": True, "data": chunks, "error": None}
```

function_name 是模型请求的 Python 函数名；params.tool_name 是文档分类。两者在分发时有不同职责。

## 任务 3：导入检查

- [x] 在项目目录执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from app.usage_tools import execute_usage_tool; print('导入成功')"
```

预期输出“导入成功”。该命令不执行工具，也不请求模型。

## 任务 4：导师离线验收

- [x] 核对源码后执行以下实验，使用模拟检索，不调用实际模型与数据库。

```python
import asyncio
import json
from unittest.mock import AsyncMock, patch

import app.usage_tools as usage_tools


async def verify():
    invalid_cases = [
        ("unknown", "{}", "UNSUPPORTED_TOOL"),
        ("search_tool_docs", "{", "INVALID_ARGUMENTS"),
        ("search_tool_docs", "[]", "INVALID_ARGUMENTS"),
        ("search_tool_docs", '{"question":"q"}', "INVALID_ARGUMENTS"),
        ("search_tool_docs", '{"question":123,"tool_name":"getinfo"}', "INVALID_ARGUMENTS"),
        ("search_tool_docs", '{"question":"q","tool_name":"unknown"}', "INVALID_ARGUMENTS"),
        ("search_tool_docs", '{"question":"q","tool_name":"getinfo","platform":"nvidia"}', "INVALID_ARGUMENTS"),
        ("search_tool_docs", '{"question":"   ","tool_name":"getinfo"}', "INVALID_ARGUMENTS"),
        ("search_tool_docs", None, "INVALID_ARGUMENTS"),
    ]
    for name, arguments, code in invalid_cases:
        search = AsyncMock()
        with patch.object(usage_tools, "search_tool_docs", search):
            result = await usage_tools.execute_usage_tool(name, arguments)
        assert result["ok"] is False and result["data"] is None
        assert result["error"]["code"] == code
        search.assert_not_awaited()

    for chunks in ([{"chunk_id": "offline-001"}], []):
        search = AsyncMock(return_value=chunks)
        arguments = json.dumps({"question": "  offline question  ", "tool_name": "getinfo"})
        with patch.object(usage_tools, "search_tool_docs", search):
            result = await usage_tools.execute_usage_tool("search_tool_docs", arguments)
        search.assert_awaited_once_with("offline question", "getinfo")
        assert result["ok"] is True and result["data"] is chunks
        assert result["error"] is None

    failure = ValueError("offline backend failure")
    with patch.object(usage_tools, "search_tool_docs", AsyncMock(side_effect=failure)):
        try:
            await usage_tools.execute_usage_tool(
                "search_tool_docs", json.dumps({"question": "q", "tool_name": "getinfo"})
            )
        except ValueError as exc:
            assert exc is failure
        else:
            raise AssertionError("Backend error must propagate to the caller")

    print("PASS: invalid inputs stopped before retrieval; valid/empty results wrapped; backend failure propagated.")


asyncio.run(verify())
```

## 完成条件与后续

错误函数名和无效参数在检索前拦截，合法请求只调用一次检索；返回片段为空时仍为 ok=true、data=[]。检索服务异常不归类为参数错误。通过离线验收后，再连接模型返回的 tool_call.function.name 与 tool_call.function.arguments，进行第一轮模型请求和消息回传。

## 自审记录

- [x] 复用类型及检索函数已经存在，本步新增函数有完整定义。
- [x] 函数名称白名单与资料分类枚举分开，参数 try 范围不包含外部执行。
- [x] 导入命令与离线实验不请求真实模型；案例覆盖有效、无效、空资料与后端失败边界。

2026-10-30 计划检查：导师在临时内存模块中执行了本计划的函数示例与模拟实验，确认上述边界通过。实际 app/usage_tools.py 中尚未添加 execute_usage_tool，学习者源码未被修改；本计划的实现任务仍待学习者完成。

2026-10-30 实际验收：学习者已完成函数并反馈导入成功。导师读取实际源码，执行了本计划的模拟实验，9 种错误输入均在检索前被拦截；有效与空片段返回成功结构，后端 ValueError 原样向上传递。本步完成，未调用真实模型或数据库。
