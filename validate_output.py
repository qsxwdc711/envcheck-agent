from pydantic import BaseModel,ValidationError
from typing import Literal
class AnalysResult(BaseModel):
    check_status:Literal["completed","failed"]
    overall_result:Literal["pass","fail","error"]
    failed_items:list[str]
    root_cause:str|None

try:
    res = AnalysResult.model_validate(
{"check_status":"completed","overall_result":"pass","failed_items":[],"root_cause":None}
    )
    print(type(res),res.failed_items,res.root_cause)
except ValidationError as exc:
    print("校验失败",exc)
print("校验流程结束")
