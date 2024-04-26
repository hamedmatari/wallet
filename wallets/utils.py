from contextlib import contextmanager

import redis
import requests
from django.conf import settings


def request_third_party_deposit():
    response = requests.post("http://localhost:8010/")
    return response.json()


class RedisLock:
    def __init__(self, lock_id, timeout=60000):
        self.lock_id = lock_id
        self.timeout = timeout

        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        self.lock_acquired = False

    def __enter__(self):
        self.lock_acquired = self.redis.set(
            self.lock_id, "true", nx=True, px=self.timeout
        )
        return self.lock_acquired

    def __exit__(self, exc_type, exc_value, traceback):
        if self.lock_acquired:
            self.redis.delete(self.lock_id)
