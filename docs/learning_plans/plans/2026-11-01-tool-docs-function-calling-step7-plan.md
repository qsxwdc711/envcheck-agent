# 三工具 Function Calling：另外两类资料范围选择回放计划

**执行方式：** 学习者每次只替换演示脚本末尾的 question，自行运行一次；导师先核对一题，再继续下一题。

**Goal:** 验证用户不提供 tool_name 时，当前流程能够选择 nic_link_check 和 aidoc_download，检索对应资料并生成有依据的最终回答。

**Architecture:** 使用现有 usage_agent_demo.py 的两次文本请求与一次工具执行流程；复用固定 RAG 问题集中的业务事实及验收标准，不修改提示词来指定本题工具。只把 question 发送给模型，人工预期不进入模型输入。

**Tech Stack:** 已完成的原生 Function Calling、Embedding、Qdrant、RagAnswer。

**修改文件：** ./usage_agent_demo.py，仅替换 __main__ 内的 question。应用模块保持现状，不增加新功能。

## 任务 1：RoCE 通用用法

- [x] 学习者将末尾 question 改为：

```python
    question = "RoCE 线序检查的基础命令怎么写，需要提供哪些参数？"
```

- [x] 在项目目录执行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\usage_agent_demo.py
```

- [x] 导师核对真实工具请求：function.name=search_tool_docs，参数 tool_name=nic_link_check。用户原句没有该工具名。
- [x] 核对片段属于 nic_link_check；最终为 sufficient，命令使用 roce_switch_check.py，说明主机列表、leaf 列表、Pod 大小与管理 IP 基准值。
- [x] 经 step9 的 Top-4 回放，核对 --switchlist 与 --switch-leaf-list 为别名，不混入 RoCE 不接受的参数；输出文件参数说明可选，数值按实际环境填写。仅引用实际支持回答的 nic-link-usage 片段。

## 任务 2：镜像制作工具中的端口映射

任务 1 核对后，再替换为以下问题。该问题复用原 T05 的映射事实，并增加镜像制作上下文，使资料范围可推断。

- [x] 学习者修改问题并按上述命令运行：

```python
    question = "制作装机镜像时，文档里系统编号 240404 对应的虚拟机端口是多少？"
```

- [x] 导师核对真实工具请求：function.name=search_tool_docs，参数 tool_name=aidoc_download。
- [x] 核对最终为 sufficient，回答端口 10022，实际引用 aidoc-usage-004，与本地 aidoc_download 片段一致；未补充无依据的现场信息。

## 完成条件与后续

三类工具各有一条自然语言输入触发正确资料范围、检索及最终回答的证据。getinfo 场景已于 2026-11-01 核对通过，另外两题在本计划逐题验收。每条正常路径预计为两次文本请求、一次 Embedding、一次本地查询，外部调用由学习者运行；导师不使用真实模型替学习者回放。

如果输出与预期不符，先依据实际轨迹区分分类、检索和生成问题，不向提示词硬编码本题答案。现有结构/引用检查通过仍需人工核对业务含义。该步骤不产生准确率或长期稳定性指标，后续再完善有界循环、资料不足回放与接口。

## RoCE 真实回放记录（2026-11-01）

学习者提供完整轨迹：search_tool_docs 请求 id=call_a212xoj3rgufy7c4lzg5j6th，参数 tool_name=nic_link_check；工具返回 ok=true、error=null，片段依次为 nic-link-usage-004、002、006。消息顺序正确，最终 sufficient，引用上述三条。脚本、现场参数需替换、输出参数可选、默认结果文件和 config.yaml 准备说明符合本次资料。路由与通用命令指导主线通过。

本题记录为有改进项：回答将 --switchlist 与 --switch-leaf-list 描述为参数不一致、需按现场版本确认，未说明当前工具中的别名关系。返回的三个片段均未明确该关系；已修订的 nic-link-usage-003 本次没有进入 Top-3。导师只读核对数据库，确认 003 的别名说明已实际入库，集合仍为 19 点（getinfo=7、nic_link_check=7、aidoc_download=5），并复核本地 RoCE 脚本第 910 行将两者注册到同一个参数。当前证据指向本次检索缺少必要说明，不把它归因为入库未更新，也不据此认定向量排序随机或全部生成规则失效。

别名验收项继续保持未完成。先补 aidoc_download 路由回放，再以本题评估候选数量或关联章节补充对证据覆盖的影响；候选更多是否足够需实测，不承诺只增加 limit 即能解决。此次只读检查没有调用真实模型或 Embedding，没有修改检索实现。

## aidoc_download 真实回放记录（2026-11-01）

学习者提供工具请求 id=call_uapo20c5wjlvx4cj03y6221d，function.name=search_tool_docs，参数为 question=系统编号 240404 对应的虚拟机端口是多少、tool_name=aidoc_download。原始自然语言问题带有制作装机镜像上下文，但未提供工具名。最终回答为 sufficient，端口 10022，仅引用 aidoc-usage-004。导师核对实际脚本末尾问题与本地 004 映射表，回答一致。本次消息未贴完整检索列表，不额外记述其排序或数量，也没有请求耗时数据。

至此，三类资料范围选择均有真实模型调用证据；getinfo 与 aidoc_download 的已测问题回答通过，RoCE 仍保留别名说明的改进项。本轮不表述为三类全部用法或稳定性验收完成。接下来按 step8 计划固定问题和向量，比较候选数量，定位必要片段在排序中的位置。

后续 step8 固定查询实验确认 003 排第 4；step9 将新工具路径设为 limit=4 后，真实回放返回 004、002、006、003，最终回答明确别名并引用 003，原别名改进项已在该题关闭。三类路由与各自已测通用问题已有通过记录，Top-4 对其他题的影响仍在 step9 逐题回归。
