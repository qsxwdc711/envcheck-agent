from pathlib import Path
import json
import re
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIR / "data" / "source_docs" / "aidoc_download.md"

raw_text = SOURCE_PATH.read_text(encoding="utf-8-sig")
clean_text = (
    raw_text
    .replace("\\.", ".")
    .replace("\\_", "_")
    .replace("\\-", "-")
    .replace("aidoc-download.py", "aidoc_download.py")
)
clean_text = clean_text.replace(
    "aidoc-download.py",
    "aidoc_download.py",
)
print("文件存在:",SOURCE_PATH.exists())
print("原文字数：", len(raw_text))
print("下载脚本名已还原：", "aidoc_download.py" in clean_text)
lines = clean_text.splitlines()

starts = [
    index
    for index,line in enumerate(lines)
    if re.match(r"^\d+\.", line)
]
starts.append(len(lines))
sections = []
for index in range(len(starts)-1):
    start = starts[index]
    end = starts[index+1]
    title = lines[start].strip()
    content = "\n".join(lines[start:end]).strip()
    sections.append({
        "section":title,
        "content":content,
    })
print("片段数量:",len(sections))
for index, section in enumerate(sections, start=1):
    print(index, section["section"], len(section["content"]))

chunks = []
for number, section in enumerate(sections, start=1):
    chunks.append({
        "chunk_id": f"aidoc-usage-{number:03d}",
        "tool_name": "aidoc_download",
        "source": SOURCE_PATH.relative_to(PROJECT_DIR).as_posix(),
        "section": section["section"],
        "source_type": "tool_manual",
        "content": section["content"],
    })
output_path = PROJECT_DIR / "data" / "tool_docs" / "aidoc_download_chunks.jsonl"
output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8") as file:
    for chunk in chunks:
        file.write(json.dumps(chunk, ensure_ascii=False) + "\n")
print("已保存片段数量：", len(chunks))
print("保存位置：", output_path)
