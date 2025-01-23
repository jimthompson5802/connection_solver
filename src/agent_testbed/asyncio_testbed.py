import asyncio
import datetime
import random


async def stub_program(x, y, sleep_time=240):
    print(f"Stub program started at {asyncio.get_event_loop().time()} - {datetime.datetime.now()}")
    print(f"processing {x}, {y} Sleeping for {sleep_time} seconds")
    await asyncio.sleep(sleep_time)
    print(f"Stub program finished at {asyncio.get_event_loop().time()} - {datetime.datetime.now()}")
    return x, y, x + y


async def main():
    random_tuples = [(random.randint(1, 100), random.randint(1, 100)) for _ in range(10)]
    print(f"Random tuples: {random_tuples}")
    tasks = [stub_program(x, y) for x, y in random_tuples]
    results = await asyncio.gather(*tasks)
    print(f"Answer: {results}")


if __name__ == "__main__":
    asyncio.run(main())
