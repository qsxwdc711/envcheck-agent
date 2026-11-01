# 三工具 Function Calling：Agent HTTP 入口计划

**执行方式：** 学习者增加一个请求模型与路由；导师先用模拟业务函数检查请求和错误映射，再核对实际实现，最后由学习者进行真实 HTTP 联调。

**Goal:** 提供 POST /agent/ask，客户端仅提交自然语言 question，响应为 RagAnswer，资料范围由业务循环中的模型决定。

**Architecture:** AgentRequest 负责请求字段与类型，路由 strip 并拒绝空白问题，随后 await run_usage_agent。业务入口已经含 90 秒共享预算，路由不套用旧 RAG 的 60 秒配置。HTTP 层转换已知超时、服务与协议/输出错误，正常 insufficient 仍为 200。现有 /tools/ask 是固定 RAG 对照入口，新业务不复用其需 tool_name 的请求模型。

**Tech Stack:** FastAPI、Pydantic 2、现有 run_usage_agent 和 RagAnswer。

## 任务 1：新增请求模型

**修改文件：** ./app/schemas.py。

- [x] 将顶部 Pydantic 导入改为：

```python
from pydantic import BaseModel, ConfigDict
```

- [x] 在文件末尾添加：

```python
class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
```

ConfigDict 是这个请求模型的 Pydantic 配置，extra=forbid 拒绝 schema 之外的字段。新入口由模型选择资料，所以客户端发送 tool_name 应返回 422，而不是让其被默默忽略。缺少字段和错误类型由 FastAPI/Pydantic 在路由执行前拦截；纯空白由后面的 strip 检查拦截。

## 任务 2：接入业务入口

**修改文件：** ./app/main.py。

- [x] 在导入区域添加：

```python
from app.schemas import AgentRequest
from app.usage_agent import run_usage_agent
```

- [x] 在已有路由后添加：

```python
@app.post("/agent/ask", response_model=RagAnswer)
async def ask_agent(request: AgentRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="问题不能为空")
    try:
        return await run_usage_agent(question)
    except (TimeoutError, ArkAPITimeoutError):
        raise HTTPException(status_code=504, detail="Agent处理超时")
    except ArkAPIError:
        raise HTTPException(status_code=502, detail="模型服务调用失败")
    except (ValidationError, ValueError, RuntimeError):
        raise HTTPException(status_code=502, detail="Agent未能完成本次处理")
```

RagAnswer、HTTPException、ValidationError 及 SDK 异常已由当前 main.py 导入。超时分支放在 ArkAPIError 前，避免 SDK 超时落入普通服务失败。最后一组包括模型结构/引用错误和流程异常，HTTP detail 使用概括性说明，不把所有 RuntimeError 都宣称为工具次数超限。未预计的错误继续按服务端异常处理，本步不保证覆盖全部基础设施故障。

## 任务 3：离线验收

- [x] 导师在进程内 ASGI 测试应用中用模拟 run_usage_agent 检查：正常/insufficient 均 200；缺字段、错误类型、额外字段、空字符串和空白均 422 且业务不执行；总预算及 SDK 超时 504；SDK 服务错误、输出校验和流程异常 502。测试不请求真实模型或启动网络监听。
- [x] 学习者完成代码后执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from app.main import app; print('/agent/ask' in app.openapi()['paths'])"
```

预期 True，仅证明路由已注册且可生成 schema，不代表接口业务已经验收。

- [x] 导师读取实际源码并以模拟依赖核对同样的 HTTP 分支和 OpenAPI 请求结构。

## 任务 4：后续真实联调

实际代码离线通过后，由学习者在已有项目终端启动或重载服务，使用当前可用的 18000 端口和 /docs。首条真实请求只包含：

```json
{
  "question": "采集服务器信息和检查 RoCE 线序这两类任务，运行前是否都需要准备主机列表文件 hostfile？请分别依据资料简要说明。"
}
```

- [x] 学习者提供 HTTP 状态及响应；导师按两类资料、hostfile 文件/参数区别、引用和最终结构核对。状态 200 与 sufficient/insufficient 的语义分别记录。

## 验收范围

本步先接入和离线检查新入口，真实 HTTP 证据在最后一步再记录。模型自行改写问题、选择工具及检索均在 run_usage_agent 内；HTTP 层不另做 Embedding、检索或模型调用。业务模块与命令行无需为新入口复制逻辑。旧固定 RAG 和历史巡检接口保留各自已有配置。

## 导师预检查记录（2026-11-01）

提取计划中的请求模型和路由到进程内 FastAPI 应用，替换业务入口，执行十三个 HTTP 情况。正常与 insufficient 均 200；缺字段、数字类型、额外 tool_name、空字符串、纯空白均 422 且不调用业务；总任务和 SDK 超时均 504；SDK 服务错误、Pydantic 校验错误、引用 ValueError 和流程 RuntimeError 均 502。问题去除首尾空白后只传一次业务入口，OpenAPI 只要求 question 且 additionalProperties=false。没有网络监听、模型或数据库请求，没有修改应用源码。实际接口仍待学习者实现与核对。

## 实际接口离线验收（2026-11-01）

学习者反馈路由检查为 True。导师读取实际 schemas.py 和 main.py，直接导入真实 app，通过 httpx.ASGITransport 替换路由绑定的 run_usage_agent，重复十三项契约检查，均符合预期。OpenAPI 只要求 question 且拒绝额外字段；无效请求不调用业务；合法问题先去除首尾空白并只调用一次业务；两个正常业务状态均为 200，错误映射为 422/504/502。旧四个路由仍注册。

这项验收没有启动网络监听、调用真实模型/Embedding/数据库、修改源码或写正式评测结果。只读检查当前 18000 端口未发现监听；下一步由学习者从已有模型环境终端启动 Uvicorn，按任务 4 进行真实请求。真实 HTTP 状态及回答尚未取得，任务 4 保持未完成。

## 真实 HTTP 联调验收（2026-11-01）

学习者在 /agent/ask 文档页提供 HTTP 200 与完整 RagAnswer，evidence_status=sufficient，引用 getinfo-usage-004、005 及 nic-link-usage-002、004。回答分别说明服务器采集与 RoCE 线序的主机列表需求，并明确 IB 场景中的免 hostfile 条件不适用于 RoCE。本条结构、引用及核心业务内容核对通过。

原样响应与验证范围已保存到 [Agent 阶段验收记录](../../tool-usage-agent-evidence.md)。状态码与响应来自学习者反馈，导师未再次调用真实服务；本条未提供耗时或服务端工具轨迹，不补写延迟或本次实际执行次数。新入口的最小端到端闭环完成，固定 RAG 旧用例不据此计为新 Agent 批量回归。
