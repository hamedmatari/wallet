import uuid

from django.db import models


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
    # todo: add fields if necessary
    pass


class Wallet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    balance = models.BigIntegerField(default=0)

    def deposit(self, amount: int):
        # todo: deposit the amount into this wallet
        pass
