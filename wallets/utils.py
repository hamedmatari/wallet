from django.db.transaction import atomic
import redis
import requests
from django.conf import settings


def request_third_party_deposit():
    response = requests.post("http://localhost:8010/")
    return response.json(), response.ok


def hit_transactions(wallet, transaction):
    from django.db.models import F

    with atomic():
        wallet.balance = F("balance") + transaction.amount
        transaction.status = "completed"
        transaction.save()
        wallet.save()


def release_lock(uuid):
    lock_key = f"wallet:{uuid}"
    lock = RedisLock(lock_key)
    lock.release()


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

    def acquire(self):
        if not self.lock_acquired:
            self.lock_acquired = self.redis.set(
                self.lock_id, "true", nx=True, px=self.timeout
            )
        return self.lock_acquired

    def release(self):
        if self.lock_acquired:
            self.redis.delete(self.lock_id)
            self.lock_acquired = False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
