# 三工具 Function Calling：工具声明实施计划

**执行方式：** 学习者逐步编写，导师核对。本步只添加给模型看的工具声明，后续分发器与调用循环分步实现。

**Goal:** 在 app/usage_tools.py 添加 SEARCH_TOOL_DOCS_TOOL，复用 ToolRagRequest 生成工具参数的 JSON Schema。

**Architecture:** Python 检索函数已返回原始片段。工具声明告诉模型函数名称、用途与合法参数结构；执行前的严格参数校验由后续分发器负责。参数结构复用现有 Pydantic 模型，避免另外维护一份资料分类枚举。

**Tech Stack:** Python、Pydantic JSON Schema、原生 Function Calling 工具定义。

**文件：** ./app/usage_tools.py。

## 任务 1：导入参数模型

- [x] 在现有导入部分增加：

```python
from app.schemas import ToolRagRequest
```

现有模型包含 question 字符串，以及限定为三个工具资料范围的 tool_name。导师已离线核对 model_json_schema() 生成的 required 和 enum。

## 任务 2：添加工具声明

- [x] 在现有 search_tool_docs 函数定义之前增加：

```python
SEARCH_TOOL_DOCS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_tool_docs",
        "description": (
            "检索内部交付运维工具使用文档，返回相关片段。"
            "采集服务器信息、生成报告选择 getinfo；"
            "IB/RoCE 线序检查选择 nic_link_check；"
            "资源下载、镜像制作与验证选择 aidoc_download。"
        ),
        "parameters": ToolRagRequest.model_json_schema(),
    },
}
```

type、function.name 和 function.parameters 沿用现有工具演示的结构。模型依据 description 选择使用范围，并按 parameters 描述生成参数。

## 任务 3：检查声明结构

- [x] 在项目目录执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from app.usage_tools import SEARCH_TOOL_DOCS_TOOL as t; f=t['function']; print(f['name']); print(f['parameters']['properties']['tool_name']['enum']); print(f['parameters']['required'])"
```

预期输出：

```text
search_tool_docs
['getinfo', 'nic_link_check', 'aidoc_download']
['question', 'tool_name']
```

该检查不执行检索函数，不调用 Embedding 或文本模型。

## 本步完成条件与后续任务

声明中的函数名与已实现的检索函数一致，参数 schema 为 object，question 和 tool_name 为必填，tool_name 包含三个合法枚举值。JSON Schema 是给模型的输入约定；程序仍需严格验证实际返回的工具参数。

下一步给分发器单独制定实施步骤：工具名称白名单、json.loads、ToolRagRequest.model_validate 的 strict 与 extra 检查、空问题检查、调用 search_tool_docs，以及 ok/data/error 包装。本步不将这些能力计为完成。

## 自审记录

- [x] 所有新增符号均在本计划中有定义，复用参数模型已在当前代码中核对。
- [x] 声明与现有原生工具格式一致，未将模型描述约定当作运行时校验。
- [x] 保留已验收的检索函数，校验命令只读取声明，不请求模型。

2026-10-30 验收：学习者提供了正确的名称、枚举和必填项输出。导师读取实际代码并离线核对声明可序列化为 JSON，名称与异步函数一致，parameters 与现有 ToolRagRequest 的 schema 一致。本步完成，没有请求模型或数据库。
