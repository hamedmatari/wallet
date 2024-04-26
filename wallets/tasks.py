from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import F
from django.db.transaction import atomic
from django.utils import timezone
from requests.exceptions import ConnectionError

from wallets.models import Transaction
from wallets.utils import (
    RedisLock,
    hit_transactions,
    request_third_party_deposit,
    release_lock,
)
from celery.exceptions import MaxRetriesExceededError

logger = get_task_logger(__name__)


@shared_task(
    name="wallet.queue_transactions",
)
def queue_transactions():
    # a better option would be to avoid making a query over Transactions to queue transactions and put them in the queue with other optimum strategy
    transaction_queue = Transaction.objects.filter(
        status="pending", scheduled_time__lte=timezone.now()
    ).order_by("transaction_type")

    for transaction in transaction_queue:
        lock_key = f"wallet:{transaction.wallet.uuid}"

        lock = RedisLock(lock_key)
        if lock.acquire():
            fire_transaction.delay(transaction_id=transaction.id)
            pass
        else:
            pass


@shared_task(
    name="wallet.fire_transaction",
    autoretry_for=(ConnectionError,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
)
def fire_transaction(transaction_id):
    transaction = Transaction.objects.select_related("wallet").get(id=transaction_id)
    wallet = transaction.wallet
    lock_key = f"wallet:{transaction.wallet.uuid}"

    if transaction.transaction_type == "deposit":
        hit_transactions(wallet=wallet, transaction=transaction)
    elif (
        transaction.transaction_type == "withdraw"
        and wallet.balance >= transaction.amount
    ):
        try:
            content, ok = request_third_party_deposit()
        except ConnectionError as e:
            transaction.status = "retrying"
            transaction.save(update_fields=["status"])
            release_lock(lock_key)
        except MaxRetriesExceededError as e:
            transaction.status = "failed"
            transaction.save(update_fields=["status"])
            release_lock(lock_key)
        if ok:
            hit_transactions(wallet=wallet, transaction=transaction)
        else:
            transaction.status = "failed"
            transaction.save(update_fields=["status"])
    else:
        transaction.status = "failed"
        transaction.save(update_fields=["status"])

    release_lock(lock_key)
