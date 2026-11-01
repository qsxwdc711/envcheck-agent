import json
with open("data/fixtures/record_1001.json","r",encoding="utf-8")as file:
    record = json.load(file)
print(record["record_id"])
print(record["server_name"])
print(record["check_status"])
print(record["overall_result"])
for i in record["checks"]:
    print(i["name"])
    print(i["actual"])
    print(i["expected"])
    print(i["result"])
