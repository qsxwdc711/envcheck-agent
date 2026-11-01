import asyncio

from app.usage_agent import run_usage_agent


if __name__ == "__main__":
    question = "采集服务器信息和检查 RoCE 线序这两类任务，运行前是否都需要准备主机列表文件 hostfile？请分别依据资料简要说明。"
    asyncio.run(run_usage_agent(question))
