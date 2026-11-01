from pathlib import Path
import json
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIR / "data" / "source_docs" / "getinfo.md"

raw_text = SOURCE_PATH.read_text(encoding="utf-8-sig")
clean_text = (
    raw_text
    .replace("\\.",".")
    .replace("\\_","_")
    .replace("\\-","-")
)
print("文件存在:",SOURCE_PATH.exists())
print("原文字数：", len(raw_text))
print("采集命令还原成功：",
      "python3 getinfo.py --username root --hostfile hostfile" in clean_text)
lines = clean_text.splitlines()

starts = [
    index
    for index,line in enumerate(lines)
    if line.startswith("# ")
]
starts.append(len(lines))
sections = []
for index in range(len(starts)-1):
    start = starts[index]
    end = starts[index+1]
    title = lines[start][2:].replace("**","").strip()
    content = "\n".join(lines[start:end]).strip()
    sections.append({
        "section":title,
        "content":content,
    })
print("片段数量:",len(sections))
for index, section in enumerate(sections, start=1):
    print(index, section["section"], len(section["content"]))

for section in sections :
    content = section["content"]
    if section["section"] =="getinfo.py 使用说明":
        content = content.replace(
            "- --expect: 期望值配置，默认 sop_expectations.json",
            "- --expect-file: 期望值配置，默认 sop_expectations.json"
            "（已按本地 getinfo.py 参数定义核对）",
        )
        content = content.replace(
            "- --username: SSH用户名（必需）",
            "- --username: SSH用户名（可选；省略时依赖SSH配置或当前用户自动检测，"
            "仍需可用的SSH认证；已按本地 getinfo.py 核对）",
        )
    elif section["section"]=="2.运行前置要求":
        content = content.replace(
            "Sudo apt pandoc",
            "生成 Word 需要安装 Pandoc，并确保执行脚本时能找到 pandoc 命令。"
            "具体安装方式按部署环境确定。（已按本地 sop_json_to_md.py 核对）",
        )
    elif section["section"]=="5.sop_json_to_md.py 使用说明":
        content = content.replace(
            r"- Word 文档已生成: getinfo/\<json文件名\>_report.docx",
            "- Word 文档：成功执行 --docx 后，在 Markdown 输出文件的同目录"
            "生成同名 .docx，例如 test26.md 对应 test26.docx。"
            "（已按本地 sop_json_to_md.py 核对）",
        )
    section["content"]=content
chunks = []
for number, section in enumerate(sections, start=1):
    chunks.append({
        "chunk_id": f"getinfo-usage-{number:03d}",
        "tool_name": "getinfo",
        "source": SOURCE_PATH.relative_to(PROJECT_DIR).as_posix(),
        "section": section["section"],
        "source_type": "tool_manual",
        "content": section["content"],
    })
output_path = PROJECT_DIR / "data" / "tool_docs" / "chunks.jsonl"
output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8") as file:
    for chunk in chunks:
        file.write(json.dumps(chunk, ensure_ascii=False) + "\n")
print("已保存片段数量：", len(chunks))
print("保存位置：", output_path)
