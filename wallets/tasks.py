from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import F
from django.db.transaction import atomic
from django.utils import timezone

from wallets.models import Transaction
from wallets.utils import RedisLock

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
)
def fire_transaction(transaction_id):
    transaction = Transaction.objects.select_related("wallet").get(id)
    wallet = transaction.wallet

    if transaction.transaction_type == "deposit":
        wallet.balance = F("balance") + transaction.amount
    elif transaction.transaction_type == "withdraw":
        if wallet.balance >= transaction.amount:
            with atomic():
                wallet.balance = F("balance") - transaction.amount
                wallet.save()
                transaction.status = "completed"
                transaction.save()
        else:
            transaction.status = "failed"
            transaction.save()

    lock_key = f"wallet:{transaction.wallet.uuid}"
    lock = RedisLock(lock_key)
    lock.release()
