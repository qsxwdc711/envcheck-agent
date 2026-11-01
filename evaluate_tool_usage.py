import asyncio
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from app.schemas import RagAnswer
import httpx

PROJECT_DIR = Path(__file__).resolve().parent


async def evaluate_one(case:dict):

    payload = {
        "question": case["question"],
        "tool_name": case["tool_name"],
    }

    async with httpx.AsyncClient(
        timeout=75.0,
        trust_env=False,
    ) as client:
        started = perf_counter()
        response = await client.post(
            "http://127.0.0.1:18000/tools/ask",
            json=payload,
        )
        elapsed = perf_counter() - started

    result = {
        "case_id": case["case_id"],
        "request": payload,
        "http_status": response.status_code,
        "elapsed_seconds": round(elapsed, 3),
        "run_status": "error",
        "response": None,
        "error": None,
        "expected_evidence_status": case["expected_evidence_status"],
        "evidence_status_match": None,
        "expected_checks": case["expected_checks"],
        "review_status": "pending",
    }

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        result["run_status"] = "http_error"
        result["error"] = {
            "type": "HTTPStatusError",
            "message": response.text,
        }
    else:
        answer = RagAnswer.model_validate_json(response.text)
        result["run_status"] = "completed"
        result["response"] = answer.model_dump()
        result["evidence_status_match"] = (
            answer.evidence_status == case["expected_evidence_status"]
        )

    output_dir = PROJECT_DIR / "eval" / "tool_usage_runs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{case['case_id']}_{uuid4().hex}.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("案例编号：", result["case_id"])
    print("HTTP 状态码：", result["http_status"])
    print("耗时（秒）：", result["elapsed_seconds"])
    print("预期状态是否一致：", result["evidence_status_match"])
    print("人工核对状态：", result["review_status"])
    print("结果文件：", output_path)
    print("运行状态：", result["run_status"])

async def main():
    cases_path = PROJECT_DIR / "eval" / "tool_usage_cases.jsonl"
    lines = cases_path.read_text(encoding="utf-8").splitlines()

    for line in lines:
        if not line.strip():
            continue

        case = json.loads(line)

        if case["case_id"] not in {"T03", "T04"}:
            continue

        await evaluate_one(case)

if __name__ == "__main__":
    asyncio.run(main())
