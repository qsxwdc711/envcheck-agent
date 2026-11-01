# 三工具 Function Calling：检索候选数量比较计划

**执行方式：** 学习者编写一个独立诊断脚本，导师先离线核对，再由学习者运行一次 Embedding 与本地检索。结果用于选择后续优化方式，不直接修改应用默认值。

**Goal:** 固定 RoCE 检索问题与同一个向量，比较 Top-3、Top-4、Top-7，确定含参数别名说明的 nic-link-usage-003 在本次排序中的位置。

**Architecture:** 重用 embed_text 与 search_tool_chunks。只对查询调用一次 Embedding，循环改变 limit 并通过 asyncio.to_thread 执行同步查询；打印片段 ID 和 003 是否命中。现有资料按 tool_name=nic_link_check 过滤，仅有 7 个点，因此 Top-7 用于观察完整候选排序，不作为最终生成配置。

**Tech Stack:** Python、asyncio、现有 Embedding 与 Qdrant 检索函数。

**拟新建文件：** ./retrieval_compare_demo.py。导师制定计划前确认该文件不存在。

## 任务 1：编写诊断脚本

- [x] 学习者新建文件并写入：

```python
import asyncio

from app.embedding_client import embed_text
from app.tool_retrieval import search_tool_chunks


async def main():
    question = "RoCE 线序检查的基础命令怎么写，需要提供哪些参数"
    query_vector = await embed_text(question)

    for limit in (3, 4, 7):
        chunks = await asyncio.to_thread(
            search_tool_chunks,
            query_vector,
            "nic_link_check",
            limit=limit,
        )
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        print(f"Top-{limit}:", chunk_ids)
        print("别名片段是否命中：", "nic-link-usage-003" in chunk_ids)


if __name__ == "__main__":
    asyncio.run(main())
```

查询文本使用前一次 RoCE 真实工具请求中的改写文本。此处直接固定它，去掉第一轮模型改写的变化；复用同一个向量，隔离 limit 的影响。新一次 Embedding 不保证与历史返回的向量逐位相同，因此此实验不能声称精确复现上次排名。

## 任务 2：离线核对与真实运行

- [x] 导师离线检查脚本语法及资源调用：一次模拟 Embedding、同一向量用于三个候选数量、过滤参数一致、每次 limit 依次为 3/4/7；不请求真实模型或数据库。
- [x] 学习者在项目终端运行：

```powershell
Set-Location "."
.\.venv\Scripts\python.exe .\retrieval_compare_demo.py
```

此脚本不请求文本生成模型、不写数据库；正常情况下仅一次外部 Embedding 请求和三次本地查询。

- [x] 学习者提供三组 ID 列表；导师核对实际源码与输出，确认 003 实际排第 4。

## 如何根据结果继续

- 若 003 排第 4，后续可以把 Top-4 作为最小候选调整进行真实问答回归，仍需检查其他题的影响，不能将该题命中等同于整体更好。
- 若 003 排第 5 至 7，说明只取四条仍不足；下一步比较更大候选集与按文档/章节关联补充。
- 若新一次查询已在 Top-3 命中 003，记录本次结果，检查与历史查询改写及排序的差异，不虚构固定第 4 名。
- 若全部七条里没有 003，先检查过滤范围、数据和集合，而不是继续增加候选数量。

先完成召回诊断，再决定应用实现调整及对应设计。当前 search_tool_chunks 默认 limit=3、工具契约和问答提示词均保持原状。

## 导师预检查记录（2026-11-01）

从本计划提取代码，在内存中用模拟 Embedding 和查询函数执行：Embedding 恰调用一次，三个查询复用同一向量对象、相同工具过滤范围，limit 依次为 3、4、7，打印三组列表及命中判断。测试中模拟将 003 放在第 4 位，仅用于检查脚本流程，不是对实际数据库排名的测量。未创建学习者脚本或改动应用源码，没有外部请求和数据库调用；实际排名仍待学习者运行。

## 真实实验验收（2026-11-01）

学习者运行脚本并提供实际结果：

| 候选数量 | chunk_id 顺序（均为 nic-link-usage 前缀） | 003 是否命中 |
| --- | --- | --- |
| 3 | 004、002、006 | false |
| 4 | 004、002、006、003 | true |
| 7 | 004、002、006、003、007、001、005 | true |

导师读取实际 retrieval_compare_demo.py，确认 Embedding 位于循环之前，三个 limit 复用同一 query_vector，工具过滤均为 nic_link_check。实际结果说明：在本次固定查询向量下，003 排第 4，Top-3 的截断导致该证据未返回，Top-4 可以覆盖。这里不新增历史查询向量相同、所有问题排名相同、答案已经改善或长期稳定的结论。

本步诊断完成。下一步按 step9 计划，在新工具调用路径显式传 limit=4，回放 RoCE 通用问题，核对实际模型改写后的查询是否仍命中 003，以及最终回答是否明确解释参数别名。应用调整及生成回归仍未执行。
