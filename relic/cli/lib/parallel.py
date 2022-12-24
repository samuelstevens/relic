import concurrent.futures

class BoundedExecutor:
    def __init__(self, pool_cls=concurrent.futures.ThreadPoolExecutor):
        self._pool = pool_cls()
        self._futures = []

    def submit(self, *args, **kwargs):
        self._futures.append(self._pool.submit(*args, **kwargs))

    def shutdown(self, **kwargs):
        self._pool.shutdown(wait=False, cancel_futures=True, **kwargs)

    def finish(self):
        return [
            future.result()
            for future in concurrent.futures.as_completed(self._futures)
        ]
