# 三工具 Function Calling：统一最终回答校验计划

**执行方式：** 学习者完成一个职责提取和两个调用点调整，导师离线核对。沿用现有分步手写方式，不运行真实模型来验证这次控制流程调整。

**Goal:** 正常生成和首轮无工具调用的最终答复，都经同一个函数校验并返回 RagAnswer。

**Architecture:** 新建 app/usage_agent.py，先承载 validate_usage_answer，后续再承载可复用执行流程。usage_agent_demo.py 通过导入调用它。首轮没有工具结果时允许引用集合为空，只有符合结构与引用规则的澄清/资料不足 JSON 能返回；非法内容抛出校验错误。检索后允许集合来自成功工具结果，沿用已有规则。本步不增加模型请求。

**Tech Stack:** Python、Pydantic、现有 RagAnswer。

**文件：** 新建 ./app/usage_agent.py；修改 ./usage_agent_demo.py。导师制定计划前确认新文件不存在。

## 任务 1：提取校验函数

- [x] 学习者在新模块写入：

```python
from app.schemas import RagAnswer


def validate_usage_answer(text: str | None, allowed_ids: set[str]) -> RagAnswer:
    result = RagAnswer.model_validate_json(text)
    if not set(result.citations).issubset(allowed_ids):
        raise ValueError("回答引用了本次检索之外的片段")
    if result.evidence_status == "sufficient" and not result.citations:
        raise ValueError("资料充足的回答必须提供至少一个引用")
    return result
```

不在校验函数内调用模型、执行检索或打印；它只依据传入文本和允许引用集合返回模型对象或抛出错误。引用属于集合仍不代表语义已经验证。

## 任务 2：接入两个调用点

- [x] 将演示脚本原有 from app.schemas import RagAnswer 替换为：

```python
from app.usage_agent import validate_usage_answer
```

- [x] 将 main 内原来的无工具调用分支替换为：

```python
    if not message.tool_calls:
        result = validate_usage_answer(message.content, set())
        print("最终回答：")
        print(result.model_dump_json(indent=2))
        return result
```

此处空集合表示本轮还没有任何成功工具结果可作引用。sufficient 无引用及伪造引用都会被拦截，不能借助这个分支跳过资料获取。

- [x] 将最终请求之后的内容读取、校验及返回部分替换为以下代码，保留前面的最终 SDK 请求：

```python
    final_message = final_completion.choices[0].message
    if final_message.tool_calls:
        raise RuntimeError("最终回答阶段不应继续请求工具")

    chunks = tool_result["data"] if tool_result["ok"] else []
    allowed_ids = {chunk["chunk_id"] for chunk in chunks}
    result = validate_usage_answer(final_message.content, allowed_ids)

    print("最终回答：")
    print(result.model_dump_json(indent=2))
    return result
```

## 任务 3：离线验收

- [x] 导师先核对计划片段：合法 sufficient/insufficient、未知引用、sufficient 空引用、非法 JSON/字段等边界符合规则；模拟首轮直接澄清与检索后回答，两个路径均返回 RagAnswer。
- [x] 学习者完成修改，在项目终端仅检查导入：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from app.usage_agent import validate_usage_answer; from usage_agent_demo import main; print('导入成功')"
```

- [x] 导师读取实际源码并使用模拟客户端核对分支返回、模型请求次数及引用边界，不调用真实模型或 Embedding。

## 完成边界

本步只统一已有最终回答的结构和引用校验。任务总预算、有界循环、累计多次工具证据、新接口与错误到 HTTP 的映射仍继续分步推进。不会把不合法模型输出自动改造成正确业务回答，语义仍需原始资料核对。

## 导师预检查记录（2026-11-01）

从本计划提取函数及替换片段，在内存中与当前演示源码组合。合法 sufficient 与 insufficient 返回 RagAnswer；未知引用、sufficient 无引用、非法 JSON、空内容和错误字段类型均拦截。另用模拟 SDK 消息核对四种流程：首轮直接澄清成功、首轮无工具却声称 sufficient 被拦截、检索后合法回答成功、检索后未知引用被拦截。两个合法路径均返回 RagAnswer，分别一/两次文本请求，工具路径保留匹配消息和 tool_choice=none，未新增模型请求。

本项仅为计划片段预检查。实际 app/usage_agent.py 尚未由导师创建，学习者实现仍待核对；未改应用源码，未调用真实模型、Embedding 或数据库。

## 实际实现验收（2026-11-01）

学习者完成新模块和两个调用点调整，反馈导入成功。导师读取实际 app/usage_agent.py 与 usage_agent_demo.py，直接调用真实校验函数检查两种合法回答与五项拒绝边界；再用模拟客户端执行实际 main 的四种流程：无工具的合法澄清、无工具却声称 sufficient、检索后合法回答、检索后未知引用。结果符合规则；两个合法路径均返回 RagAnswer，文本请求数仍分别为一次/两次，工具消息匹配且最终请求保持 tool_choice=none。

验证没有使用真实模型、Embedding 或数据库，导师未修改应用源码。本步统一返回完成，下一步给整条 main 调用链增加任务总预算，再推进可复用有界循环。
