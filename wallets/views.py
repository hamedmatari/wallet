from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.models import Wallet
from wallets.serializers import (
    WalletSerializer,
    ScheduleWithdrawSerializer,
    CreateDepositSerializer,
)


class CreateWalletView(CreateAPIView):
    serializer_class = WalletSerializer


class RetrieveWalletView(RetrieveAPIView):
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()
    lookup_field = "uuid"


class CreateDepositView(APIView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        serializer = CreateDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = Wallet.objects.get(uuid=uuid)
        wallet.make_transaction(
            amount=serializer.validated_data["amount"], type="deposit"
        )
        wallet.refresh_from_db()
        return Response({"status": "Deposit successful", "balance": wallet.balance})


class ScheduleWithdrawView(APIView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        serializer = ScheduleWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = Wallet.objects.get(uuid=uuid)
        wallet.make_transaction(
            amount=serializer.validated_data["amount"],
            type="withdraw",
            schedule_time=serializer.validated_data["scheduled_time"],
        )
        return Response({"status": "Withdrawal scheduled successfully"})
