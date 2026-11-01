# 原生工具调用助手：阶段验收记录

记录日期：2026-11-01。当前范围为面向交付运维团队的本地知识助手个人项目，支持三类文档检索与使用指导。

## 已实现的调用链

HTTP 客户端仅提交 question → AgentRequest 与路由校验 → run_usage_agent 提供共享预算 → 模型生成 search_tool_docs 调用及资料范围 → 程序严格校验并执行 Embedding/Qdrant → 回填 assistant/tool 消息并累计引用 ID → 模型最终回答 → RagAnswer 与引用范围校验 → HTTP 响应。

模型每轮最多一个工具请求，任务最多两次工具执行、三次文本请求，第三次禁止工具；共享预算 90 秒。新工具路径按 tool_name 过滤，显式返回最多四条片段。核心实现见 [业务入口](../app/usage_agent.py)、[检索工具](../app/usage_tools.py)、[HTTP 入口](../app/main.py)。

## 验证来源

| 验证 | 证据与范围 |
| --- | --- |
| 三类资料范围选择 | getinfo、nic_link_check、aidoc_download 均有学习者提供的真实模型调用记录。 |
| Top-4 回归 | RoCE 通用问题补齐 003 并明确别名；现场配置不足保持 insufficient；getinfo Word 与 aidoc 端口问题回归通过。 |
| 有界流程离线检查 | 七种模拟场景覆盖早返回、两轮引用、次数上限、同轮多个调用、错误恢复及未知引用；预算和迁移另有模拟验证。 |
| 命令行跨工具真实回放 | 实际日志显示 auto/auto/none 三次文本请求，先 getinfo 再 nic_link_check，两次成功检索，最终五条引用覆盖两轮。 |
| 实际 HTTP 层离线检查 | 十三种进程内请求验证 200/422/504/502、只接收 question、非法输入不进入业务。 |
| 新接口真实联调 | 学习者在 Swagger 提供 HTTP 200 与下方响应；两类资料均被引用。 |

具体步骤见 [原生工具调用设计与验收](learning_plans/specs/2026-10-30-tool-docs-function-calling-design.md)及其实施计划。

## POST /agent/ask 真实联调

来源：学习者在本次对话中提供的状态码与完整响应，导师没有再次发起真实请求。请求场景为本轮任务中的 getinfo/RoCE hostfile 对比；下面的请求体是该任务给出的模板，学习者没有另外粘贴 HTTP 原始请求。

```json
{
  "question": "采集服务器信息和检查 RoCE 线序这两类任务，运行前是否都需要准备主机列表文件 hostfile？请分别依据资料简要说明。"
}
```

报告的 HTTP 状态码：200。原样记录响应：

```json
{
  "answer": "需要，两类任务运行前都需要准备主机列表文件 hostfile，但依据和作用不同。\n\n1. 采集服务器信息（getinfo）：资料明确将 hostfile 列为“必需”输入文件，每行一个目标主机 IP；运行时通过 --hostfile 参数指定路径，脚本据此确定要采集哪些服务器。\n\n2. 检查 RoCE 线序（nic_link_check）：资料说明 RoCE 环境下在 CPU 上执行命令需要参数 --hostfile PATH（同时还需 --switch-leaf-list 和 --switch-base-manage-ip 等）；RoCE 模式示例命令中也包含 --hostfile hostfile。注意资料中“在 GPU 上执行命令不需 hostfile”是针对 IB 环境的说明，不适用于 RoCE 线序检查。",
  "evidence_status": "sufficient",
  "citations": [
    "getinfo-usage-004",
    "getinfo-usage-005",
    "nic-link-usage-002",
    "nic-link-usage-004"
  ]
}
```

人工核对：两类任务的 hostfile 要求有对应资料支持；每行一个 IP 对应 getinfo 输入章节，RoCE 前置条件和命令示例对应线序资料。回答将 IB 的免 hostfile 情形限制在 IB 场景，未推广为 RoCE。四个引用分别支持两类陈述，最终为 sufficient，核心验收通过。本次响应没有出现上一条 CLI 回放中“均须显式填写 --hostfile”的绝对措辞。

## 结论范围与后续

当前本地原生 Function Calling、RAG、FastAPI 最小业务闭环完成。本次 HTTP 消息没有耗时或工具轨迹，不能据此补写该请求的实际调用次数或延迟；调用次数的真实证据来自此前独立命令行日志。没有员工提效、公司上线、生产使用或整体准确率指标。

原固定 RAG 六题及其回放保留在原目录，不计为新 Agent 接口已经批量验收。当前仅提供工具使用指导，工具调用实际执行的是文档检索；向量库仍是本地模式，飞书链接正文缺口保留。后续先验收项目口述，再推进新接口固定回放、工作流框架及 MCP/Skill 等学习目标。
