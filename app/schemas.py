from pydantic import BaseModel, ConfigDict
from typing import Literal
class AnalysRequest(BaseModel):
    record_id:int

class AnalysResult(BaseModel):
    check_status:Literal["completed","failed"]
    overall_result:Literal["pass","fail","error"]
    failed_items:list[str]
    root_cause:str|None

class RagAnswer(BaseModel):
    answer:str
    evidence_status:Literal["sufficient","insufficient"]
    citations:list[str]

class RagRequest(BaseModel):
    question:str
    platform:Literal["nvidia","ascend"]

class ToolRagRequest(BaseModel):
    question:str
    tool_name:Literal["getinfo","nic_link_check","aidoc_download"]

class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
