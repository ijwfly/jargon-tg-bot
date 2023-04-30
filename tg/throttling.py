import asyncio
from collections import defaultdict


class ThrottlingDispatcher:
    def __init__(self):
        self.sleep_time = 3
        self.user_id_calls = defaultdict(lambda: None)

    async def wait_for_last_request(self, user_id):
        previous_task = self.user_id_calls[user_id]
        if previous_task and not previous_task.done():
            previous_task.cancel()

        current_task = asyncio.create_task(asyncio.sleep(self.sleep_time))
        self.user_id_calls[user_id] = current_task
        try:
            await current_task
            return True
        except asyncio.CancelledError:
            return False
