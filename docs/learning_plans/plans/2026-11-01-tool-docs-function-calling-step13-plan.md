# 三工具 Function Calling：跨工具真实回放计划

**执行方式：** 学习者仅替换演示问题，自行运行真实模型；导师根据调用轨迹和最终资料依据验收，不由导师执行外部模型请求。

**Goal:** 验证真实模型能按需求分轮检索 getinfo 与 nic_link_check，并在最终 JSON 中分别给出有依据的说明。

**Architecture:** 复用已通过离线验收的单客户端循环、两次工具上限、三次文本请求上限、累计引用和 90 秒总预算。问题不直接提供两个 tool_name，模型根据自然语言判断资料范围，先后顺序不限。

**修改文件：** ./usage_agent_demo.py，仅替换 __main__ 中 question。

## 任务 1：设置跨工具问题

- [x] 学习者将末尾问题替换为：

```python
    question = "采集服务器信息和检查 RoCE 线序这两类任务，运行前是否都需要准备主机列表文件 hostfile？请分别依据资料简要说明。"
```

本题仅验证两类资料的获取与依据，不要求生成长命令或完整项目方案。当前 getinfo 文档有 hostfile 输入/参数说明，RoCE 文档有前置条件与参数说明，业务事实有本地资料支持。

## 任务 2：真实运行

- [x] 学习者在项目目录执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\usage_agent_demo.py
```

正确完成两类文档获取的路径应包含：第一轮检索其中一类，第二轮检索另一类，第三轮 none 下输出最终 JSON。两次工具均为 search_tool_docs，但 tool_name 分别为 getinfo 与 nic_link_check；正常路径还包括两次 Embedding 和两次本地查询。

- [x] 学习者提供各轮文本请求日志、两次工具请求及最终回答，记录实际模型行为；若出现错误则保留轨迹，不改写为成功记录。

## 任务 3：人工核对

- [x] 两次工具资料范围分别覆盖 getinfo 和 nic_link_check，顺序可交换，每轮至多一个调用。
- [x] 请求数不超过三，执行数不超过二，第三次设 none；消息中保留两轮对应的 assistant/tool。
- [x] 最终分别回答两类任务的 hostfile 要求，核心结论有本次片段支持；返回 sufficient。getinfo 参数是否需显式填写的措辞保留备注，见验收记录。
- [x] 引用同时支持两类陈述，例如 getinfo-usage-004/005 与 nic-link-usage-002/003/004 中实际使用的片段；不要求引用所有返回片段。

## 偏离预期时的定位

先区分模型选错资料范围、反复检索同类、同轮多个调用、检索遗漏依据、最终生成不完整或预算耗尽。程序仍应守住现有上限。此回放不调整上限、不自动增加重试或预算；出现问题后先依据日志判断下一步。

本次为命令行真实联调，不产生 HTTP 状态码。没有耗时测量时不填写性能数字，单条成功不作为跨工具问题整体准确率。业务执行函数抽取与新接口接入在本题核对后继续。

## 真实回放验收（2026-11-01）

日志来源：学习者粘贴的原始日志（本地附件未发布）。导师读取实际演示问题并解析日志，核对结果如下：

| 轮次 | tool_choice | 行为与片段 |
| --- | --- | --- |
| 1 | auto | 调用 search_tool_docs，id=call_1fk2nh0ve2kouiukqdfjp5nr，tool_name=getinfo；返回 getinfo-004、005、003、007 四条。 |
| 2 | auto | 调用 search_tool_docs，id=call_cskkhqbu1xd4mz7ooxavs1x6，tool_name=nic_link_check；返回 nic-link-002、007、003、004 四条。 |
| 3 | none | 无工具请求，生成最终 JSON，sufficient；引用 getinfo-004、005 与 nic-link-002、003、004。 |

两条工具结果均 ok=true、error=null，共八个不同 ID。日志中的消息顺序先为 system/user/assistant/tool，再为 system/user/assistant/tool/assistant/tool；最终五条引用来自两轮资料。导师使用实际 validate_usage_answer 校验日志里的最终对象，结构与引用集合检查通过；没有重新请求模型或 Embedding。

主体业务结论通过：getinfo 的输入章节要求准备每行一个 IP 的 hostfile，RoCE 前置条件及参数章节要求提供主机列表。表述备注：回答中“标准采集模式命令示例均需通过 --hostfile 指定”过于绝对，005 中既有默认 hostfile 说明，也有未显式填写该参数的命令；本地 getinfo.py 第 3612 行将其默认值设为 hostfile。准确说法是需要准备主机列表文件，可用 --hostfile 指定路径，也可以使用默认文件配置。该备注不否定两类资料获取与跨轮引用验证，记录为调用流程通过、参数表达有改进建议。

没有请求耗时或 HTTP 数据，不新增性能指标。命令行跨工具联调完成；下一步先核对学习者对累计引用集合的理解，再抽取可复用业务入口并接 FastAPI。

累计集合理解检查：学习者正确判断每轮重新赋值会导致最终跨轮引用报错，但将原因描述为“重新读取”。导师补充准确机制：赋值覆盖 allowed_ids，第二轮会丢掉第一轮 ID；赋值本身不会重新执行检索。后续迁移继续保留 update，源码及模拟/真实回放证据均支持该机制。
