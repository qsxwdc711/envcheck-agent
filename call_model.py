import os
from arkruntime import Ark
import json
with open("data/fixtures/record_1002.json","r",encoding="utf-8")as file:
    record = json.load(file)
messages = [
    {"role":"system","content":"作为巡检分析助手，仅依据输入描述事实；无法确认的根因，在 root_cause 字段中统一用 null 表示:只返回一个合法json对象,包含下表中的四个字段,1.check_status类型:字符串,含义:保留输入中的任务执行状态。2.overall_result类型:字符串,含义:保留输入中的业务巡检结果。3.failed_items类型:字符串列表,含义:明确未通过的检查项名称。4.root_cause类型:字符串或null,含义:输入没有可靠根因证据时，返回 null。字段内容根据输入记录确定,不附加Markdown代码围栏或前后说明"},  {"role":"user","content":json.dumps(record, ensure_ascii=False)}]

client = Ark.volc(
    api_key=os.environ["ARK_API_KEY"],
    timeout=60.0,
    max_retries=0,
)

completion = client.chat.completions.create(
    model=os.environ["ARK_MODEL"],
    messages=messages,
)
text = completion.choices[0].message.content
res = json.loads(text)
print(type(res),res["failed_items"],res["root_cause"])
print(completion.choices[0].message.content)
