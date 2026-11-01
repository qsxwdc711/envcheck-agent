# 三工具 Function Calling：Top-4 生成回放计划

**执行方式：** 学习者完成一个调用参数调整，再逐题真实回放；导师读取源码和轨迹验收。沿用已确认的分步手写方式，不由导师直接修改应用源码。

**Goal:** 在新工具检索路径试取四条资料，核对 RoCE 通用问题是否获得 003，并在最终回答中正确解释 leaf 列表参数的别名关系。

**Architecture:** 真实固定查询实验显示 003 排第 4，因此 search_tool_docs 显式向底层传入 limit=4。模型工具参数契约仍为 question、tool_name，候选数量属于程序侧检索配置，不交给模型填写。底层默认值、现有固定 RAG 接口和提示词本步不调整。回放检查实际查询、片段及回答，区别召回改善与生成改善。

**Tech Stack:** 现有 Function Calling、asyncio.to_thread、Qdrant、RagAnswer。

## 任务 1：调整新工具路径的检索数量

**修改文件：** ./app/usage_tools.py。

- [x] 学习者仅将 search_tool_docs 内部的检索调用改为：

```python
    chunks = await asyncio.to_thread(
        search_tool_chunks,
        query_vector,
        tool_name,
        limit=4,
    )
```

asyncio.to_thread 会把 limit 这个关键字参数转交给 search_tool_chunks；它不是模型工具参数，不能加入 ToolRagRequest 或要求模型生成。该配置应用于调用 search_tool_docs 的三个资料范围，后续需回放另外两类问题以检查影响。

## 任务 2：先回放 RoCE 通用问题

**修改文件：** ./usage_agent_demo.py，末尾问题。

- [x] 替换末尾问题：

```python
    question = "RoCE 线序检查的基础命令怎么写，需要提供哪些参数？"
```

- [x] 学习者运行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\usage_agent_demo.py
```

- [x] 导师读取实际源码与真实输出，检查 function.name=search_tool_docs、tool_name=nic_link_check 和模型实际改写的问题。
- [x] 返回片段包含 nic-link-usage-003；最终 sufficient，明确 --switchlist 与 --switch-leaf-list 是别名，并引用 003 支持该陈述。
- [x] 若说明结果路径，保持可选性；示例 Pod/IP 等仍明确按现场替换，不混入 RoCE 不接受的参数。

该题固定向量诊断中 003 排第 4，但实际工具调用可能重写检索问题，所以新的返回集合需据实检查。若 003 未返回，先定位本次查询与排名，不能直接判定回放通过。

## 任务 3：后续逐题回归

先验收通用问题，再继续下列问题；沿用同一命令逐次运行，不一次性交付批量实现。

- [x] RoCE 现场配置不足问题，核心行为通过，模板措辞保留改进建议：

```python
    question = "这批 RoCE 服务器的 Pod 大小和管理 IP 基准值分别是多少？请直接给出最终可执行命令。"
```

预期 insufficient，不把手册中的示例数值当成现场实际值；若解释别名需有本次资料支持，输出参数若提及须说明可选。

- [x] getinfo 问题：

```python
    question = "我已经采集得到一个 SOP JSON 文件，想把它生成 Word 报告，应该怎么做？"
```

预期选择 getinfo、sufficient，使用正确脚本及参数，命令标注待替换项，Word 用法有 006 引用。

- [x] aidoc_download 问题：

```python
    question = "制作装机镜像时，文档里系统编号 240404 对应的虚拟机端口是多少？"
```

预期选择 aidoc_download、sufficient，端口 10022，引用 aidoc-usage-004。

## 验收边界

固定查询诊断、limit=4 实施和四题真实回归均完成：RoCE 通用指导、getinfo Word、aidoc 端口通过，RoCE 现场配置不足核心行为通过并保留模板措辞建议。本轮候选调整验收收尾，结论限已记录问题，不声明所有问题或长期稳定性更优。总预算、有界循环和新接口仍是后续工作。

## RoCE Top-4 真实回放验收（2026-11-01）

学习者提供完整调用轨迹：id=call_62pz1520gkt2bgu7yxlejyup，function.name=search_tool_docs，参数 tool_name=nic_link_check，改写问题为“RoCE 线序检查的基础命令怎么写，需要提供哪些参数”。工具执行 ok=true，error=null，返回片段依次为 004、002、006、003。

最终结果为 sufficient，引用 004、002、003；明确 --switchlist 与 --switch-leaf-list 是同一必填参数的别名，每行对应交换机名称/SysName；Pod 参数按每台 leaf 对应机器数解释，管理 IP 作为 index 计算基准；输出路径标为可选；所有示例文件名、IP 和数量均要求按实际环境替换。没有引用未实际用于本次陈述的 006，引用范围及核心业务内容核对通过。

导师读取当前 app/usage_tools.py，确认 search_tool_docs 显式向 search_tool_chunks 传 limit=4；当前演示问题与回放一致。本题由 Top-3 遗漏必要证据、固定向量定位第四名，到 Top-4 补齐证据并改正最终别名说明，已形成诊断与回归记录。该结论限本题，尚未记录其他题的回归或整体性能指标。导师未修改应用源码、未调用真实模型或 Embedding。

## RoCE 现场配置不足回放（2026-11-01）

学习者提供请求 id=call_j0eyuh0574tksggrwylx6nyj，function.name=search_tool_docs，tool_name=nic_link_check，改写查询为“RoCE 服务器 Pod 大小和管理 IP 基准值 可执行命令”。最终 insufficient，引用 004、003、002；明确 64 与 192.0.2.5 为文档示例，不能用于确定本批配置，Pod 与管理 IP 两项使用待填写占位符。未把示例数值冒充现场实际参数，核心资料不足边界通过。

措辞备注：回答称“可执行的命令模板”，虽然随后明确占位符需填写、不能使用示例值，仍建议改称“待填写的命令模板”，避免读者误解为已经可以原样运行。本项记为表达改进建议，不据此认定模型已经猜填配置或整个反例失败。

导师读取当前演示问题、结果校验及工具的 limit=4 设置，与回放一致。本次没有完整检索列表或耗时，不新增片段排序或性能数据，也未修改提示词或应用代码。接下来 getinfo 与 aidoc_download 两条沿用相同操作手工依次回放，可一起提交输出，无需添加批量代码。

## getinfo 与 aidoc_download 回归收尾（2026-11-01）

getinfo 请求 id=call_l7pwbwh51mqe7d40aiougs8y，选择 getinfo，改写问题为“采集得到的 SOP JSON 文件如何生成 Word 报告”。最终 sufficient，引用 006、002、003。脚本、--json、--docx、--expect 与 Word 同目录同名说明正确；新增 Pandoc 前置要求由本地 getinfo-usage-003 明确支持，参考样式文件及输入文件按实际替换。核心业务核对通过。

aidoc 请求 id=call_vncidmwm0kdbvq3q5rbxmnuc，选择 aidoc_download，改写问题为“系统编号 240404 对应的虚拟机端口”。最终 sufficient，仅引用 aidoc-usage-004，回答 10022，与本地映射一致。核对通过。

本次未贴两题完整检索列表或耗时，不新增候选排序、性能或准确率数字。当前 app/usage_tools.py 仍显式设置 limit=4，演示代码保留结构与引用范围校验。四题核心验收完成，模板措辞建议继续保留，接下来统一最终回答校验与无工具调用分支，再推进有界循环和接口。
