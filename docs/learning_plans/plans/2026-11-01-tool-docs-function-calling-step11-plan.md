# 三工具 Function Calling：任务总预算计划

**执行方式：** 学习者添加入口包装函数并修改命令行调用，导师使用模拟 main 离线检查，不要求真实模型重跑。

**Goal:** 让一次问题处理的 main 调用链共用 90 秒预算，成功时原样返回 RagAnswer，预算超时时抛出 TimeoutError。

**Architecture:** 在 usage_agent_demo.py 中通过 asyncio.timeout 包裹 await main(question)，保留各 SDK 调用已有的单次配置。命令行改为执行包装函数。以后抽取可复用执行器时再将预算迁移到业务入口；当前 FastAPI 接口尚未使用这个包装函数。

**Tech Stack:** Python 3.13、asyncio.timeout、现有 RagAnswer 返回。

**修改文件：** ./usage_agent_demo.py。

## 任务 1：设置任务预算

- [x] 在导入之后、main 定义之前添加：

```python
TASK_TIMEOUT_SECONDS = 90.0
```

## 任务 2：增加包装函数

- [x] 在 main 结束后、if __name__ 入口之前添加下列顶层函数，async def 本身不缩进：

```python
async def run_with_timeout(question: str):
    async with asyncio.timeout(TASK_TIMEOUT_SECONDS):
        return await main(question)
```

return 保留 main 的 RagAnswer；异常继续向调用方传播，不能吞掉超时后返回 None。asyncio.timeout 在此上下文取消当前异步任务的等待，并在外部表现为 TimeoutError。它不是强制停止后台同步线程的机制；to_thread 中已经开始的数据库查询仍可能继续收尾，因此不声明所有资源必在整 90 秒前停止。

## 任务 3：替换命令行调用

- [x] 文件末尾保留当前问题，将 asyncio.run(main(question)) 改为：

```python
    asyncio.run(run_with_timeout(question))
```

假设首轮文本请求耗时 40 秒、Embedding 20 秒，预算已使用约 60 秒，后续生成仅余约 30 秒；各次 SDK 请求都小于 60 秒不代表整条任务小于 90 秒。数字仅用于讲解，不是实测性能记录。

## 任务 4：离线验收

- [x] 导师从计划提取包装函数，用模拟 main 核对：成功原样返回同一个 RagAnswer；多个阶段累计超时会抛 TimeoutError；主任务的非超时异常原样传播。
- [x] 学习者完成修改并执行导入检查：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe -c "from usage_agent_demo import run_with_timeout; print('导入成功')"
```

- [x] 导师读取实际源码并临时调小测试预算，使用模拟 main 验证结果传递与超时，测试值不写回源文件，也不调用真实模型或 Embedding。

## 完成边界

本步在命令行任务入口增加共享预算。现有 main 仍为一次工具执行的固定流程，多轮工具循环、累计证据、重构后的业务入口与 FastAPI 新接口继续分步推进。总预算初值需在后续真实运行中评估；本步离线检查不产生真实服务耗时指标。

## 导师预检查记录（2026-11-01）

提取计划常量与函数，在内存中接入模拟 main：成功路径返回同一个 RagAnswer 对象且问题参数传递正确；原 ValueError 不被吞掉；三个模拟阶段共用临时测试预算，累计等待超过预算后抛出 TimeoutError，协程 finally 得到执行。测试预算仅在测试命名空间调小，未写入任何源文件。没有创建或改动应用源码，没有真实模型、Embedding 或数据库调用。该检查不验证后台线程的强制取消，实际学习者实现仍待验收。

## 实际实现验收（2026-11-01）

学习者完成包装函数与入口替换并反馈导入成功。导师读取实际源码，用模拟 main 调用真实 run_with_timeout：成功原样返回同一 RagAnswer，问题正确转交；原 ValueError 保持同一异常对象；临时缩短预算后多个模拟阶段累计等待触发 TimeoutError，协程 finally 执行。测试后常量恢复 90 秒，未改源文件或访问真实服务。

本步命令行任务总预算完成。下一步将 main 的固定两次请求合并为单客户端有界循环，沿用该预算包装；业务函数抽取与接口预算接入仍待完成。
