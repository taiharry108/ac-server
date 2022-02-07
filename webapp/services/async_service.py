from ast import AsyncFunctionDef
import asyncio
import dataclasses
from typing import Iterable


@dataclasses.dataclass
class AsyncService:
    num_workers: int
    delay: float

    async def _producer(self, in_q: asyncio.Queue, out_q: asyncio.Queue, async_func: AsyncFunctionDef,**kwargs):
        while True:
            item = await in_q.get()

            if item is None:
                # this is the final item
                await in_q.put(None)
                await out_q.put(None)
                break

            result = await async_func(**item, **kwargs)
            await asyncio.sleep(self.delay)
            await out_q.put(result)

    async def _consumer(self, q: asyncio.Queue):
        count = 0
        while True:
            item = await q.get()

            if item is None:
                count += 1
            else:
                yield item
            if count == self.num_workers:
                break

    async def work(self, items: Iterable, async_func: AsyncFunctionDef, **kwargs):
        prod_queue = asyncio.Queue()
        con_queue = asyncio.Queue()

        for item in items:
            await prod_queue.put(item)

        await prod_queue.put(None)

        [asyncio.create_task(
            self._producer(prod_queue, con_queue, async_func, **kwargs)) for _ in range(self.num_workers)]

        async for item in self._consumer(con_queue):
            yield item
