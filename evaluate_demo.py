from time import perf_counter
from tool_call_demo import run_with_timeout
import json
from pathlib import Path
from uuid import uuid4
import asyncio

PROJECT_DIR = Path(__file__).resolve().parent
async def evaluate_one(case_id:str,question:str)->dict:
    started = perf_counter()
    answer = None
    run_status = "error"
    error = None
    try:
        answer = await run_with_timeout(question)
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError("模型没有返回有效正文")
        run_status = "completed"
    except TimeoutError:
        run_status = "timeout"
        error = {
            "type":"TimeoutError",
            "message":"任务执行超时",
        }
    except Exception as exc:
        run_status = "error"
        error = {
            "type":type(exc).__name__,
            "message":str(exc)
        }
    return {
        "case_id": case_id,
        "question": question,
        "answer": answer,
        "run_status": run_status,
        "error": error,
        "elapsed_seconds": round(perf_counter() - started, 3),
    }

def save_run(result:dict)->Path:
    output_dir = PROJECT_DIR/"eval"/"runs"
    output_dir.mkdir(parents=True,exist_ok=True)
    file_name = f"{result['case_id']}_{uuid4().hex}.json"
    output_path = output_dir / file_name
    output_path.write_text(
        json.dumps(result,ensure_ascii=False,indent = 2),
        encoding="utf-8",
    )
    return output_path

def load_cases() -> list[dict]:
    cases_path = PROJECT_DIR / "eval" / "cases.jsonl"
    cases = []

    with cases_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            cases.append(json.loads(line))

    return cases
async def main():
    cases = load_cases()
    for case in cases:
        for repeat_index in range(1, 3):
            result = await evaluate_one(case["case_id"], case["question"])
            result["repeat_index"] = repeat_index
            result["expected_checks"] = case["expected_checks"]
            output_path = save_run(result)
            print("案例编号:",result["case_id"])
            print("第几次:",repeat_index)
            print("运行状态:", result["run_status"])
            print("耗时（秒）:", result["elapsed_seconds"])
            print("结果文件:", output_path)

if __name__ == "__main__":
    asyncio.run(main())
