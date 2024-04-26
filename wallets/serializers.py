from rest_framework import serializers

from wallets.models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ("uuid", "balance")
        read_only_fields = ("uuid", "balance")


class ScheduleWithdrawSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    wallet = serializers.UUIDField()
    scheduled_time = serializers.DateTimeField()


class CreateDepositView(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    wallet = serializers.UUIDField()
