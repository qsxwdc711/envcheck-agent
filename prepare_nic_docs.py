from pathlib import Path
import json
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIR / "data" / "source_docs" / "nic_link_check.md"

raw_text = SOURCE_PATH.read_text(encoding="utf-8-sig")
clean_text = (
    raw_text
)
print("文件存在:",SOURCE_PATH.exists())
print("原文字数：", len(raw_text))
print("RoCE命令存在：",
      "python3 nic_link_check/roce_switch_check.py" in clean_text)
lines = clean_text.splitlines()

starts = [
    index
    for index,line in enumerate(lines)
    if line.startswith(("# ", "### "))
]
starts.append(len(lines))
sections = []
for index in range(len(starts)-1):
    start = starts[index]
    end = starts[index+1]
    title = lines[start].lstrip("#").replace("**", "").replace("\\.", ".").strip()
    content = "\n".join(lines[start:end]).strip()
    sections.append({
        "section":title,
        "content":content,
    })
print("片段数量:",len(sections))
for index, section in enumerate(sections, start=1):
    print(index, section["section"], len(section["content"]))

for section in sections:
    if section["section"] == "5. 输出结果说明":
        content = section["content"]

        content = content.replace(
            "- 默认会生成结果文件：`_check_result.json`。",
            "- 未指定输出路径时，RoCE 默认生成 "
            "`linkcheck_<时间戳>.json`，IB 默认生成 "
            "`ib_switch_check_<时间戳>.json`；"
            "两者均可通过 `--switch-result-file` 指定输出路径。"
            "（已按本地两份线序检查脚本核对）",
        )

        content = content.replace(
            "`summary`：通过/失败/总数",
            "`issue_report.summary`：问题统计，"
            "具体字段以所选模式的实际输出为准",
        )

        section["content"] = content
    elif section["section"] == "2. 常用参数":
        content = section["content"]
        content = content.replace(
            "- `--check-switch-port`：仅执行线序检查。",
            "- 通过入口脚本区分网络类型："
            "RoCE 使用 `roce_switch_check.py`，"
            "IB 使用 `ib_switch_check.py`。",
        )
        content = content.replace(
            "- `--switch-network-type {roce,ib}`：选择网络类型。",
            "- RoCE 独立脚本不接受 `--check-switch-port` 和 "
            "`--switch-network-type`；IB 脚本保留这两个兼容参数，"
            "其中 `--switch-network-type` 仅接受 `ib`。"
            "（已按本地两份脚本的参数定义核对）",
        )
        content = content.replace(
            "- `--switch-leaf-list PATH`：leaf 列表文件",
            "- `--switchlist PATH` / `--switch-leaf-list PATH`："
            "同一必填参数的两个别名，指定 leaf 列表文件",
        )

        content = content.replace(
            "- `--switch-result-file FILE`：指定结果 JSON 文件名。",
            "- `--switch-result-file FILE`：可选，指定结果 JSON 文件路径；"
            "省略时按所选模式自动生成结果文件。",
        )
        section["content"]=content
chunks = []
for number, section in enumerate(sections, start=1):
    chunks.append({
        "chunk_id": f"nic-link-usage-{number:03d}",
        "tool_name": "nic_link_check",
        "source": SOURCE_PATH.relative_to(PROJECT_DIR).as_posix(),
        "section": section["section"],
        "source_type": "tool_manual",
        "content": section["content"],
    })
output_path = PROJECT_DIR / "data" / "tool_docs" / "nic_link_check_chunks.jsonl"
output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8") as file:
    for chunk in chunks:
        file.write(json.dumps(chunk, ensure_ascii=False) + "\n")
print("已保存片段数量：", len(chunks))
print("保存位置：", output_path)
