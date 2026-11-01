from pathlib import Path
import json

def load_record(record_id:int):
    file_path = FIXTURES_DIR /f"record_{record_id}.json"
    with open(file_path,"r",encoding="utf-8")as file:
        res = json.load(file)
    return res

PROJECT_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_DIR /"data"/"fixtures"
