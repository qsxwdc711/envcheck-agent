import asyncio,time
async def mock_model(name):
    print(name,"开始")
    await asyncio.sleep(1)
    print(name,"结束")
    return name


async def main():
    start = time.perf_counter()
    results = await asyncio.gather(
        mock_model("A"),
        mock_model("B"),
        mock_model("C"),
    )

    elapsed = time.perf_counter()-start
    print("总耗时:",elapsed,"秒")
    print("返回结果:",results)

asyncio.run(main())
