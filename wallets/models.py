import uuid

from django.db import models
from django.db.models import F

from wallets.utils import RedisLock


class Transaction(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    TYPES_CHOICES = (("withdraw", "Withdraw"), ("deposit", "Deposit"))
    amount = models.BigIntegerField()
    wallet = models.ForeignKey(
        "wallets.Wallet", on_delete=models.CASCADE, related_name="transactions"
    )
    status = models.CharField(choices=STATUS_CHOICES, default="pending", max_length=20)
    transaction_type = models.CharField(
        choices=TYPES_CHOICES, max_length=20, default="deposit"
    )
    scheduled_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Wallet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    balance = models.BigIntegerField(default=0)

    def make_transaction(self, amount, type, schedule_time=None):

        transaction = Transaction.objects.create(
            amount=amount,
            wallet=self,
            status="pending",
            transaction_type=type,
            scheduled_time=schedule_time,
        )

        if type == "deposit":
            with RedisLock(f"wallet:{self.uuid}") as acquired:
                if acquired:
                    self.balance = F("balance") + amount
                    self.save()
                    transaction.status = "completed"
                    transaction.save()
