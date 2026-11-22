from decimal import Decimal

from django.db import transaction
from django.db.models import Case, F, Sum, When
from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import CanAccessCompany, IsCompanyAdmin
from companies.models import Membership
from .models import Payment
from .serializers import PaymentSerializer


def check_balance(document, delta, exclude_payment=None):
    payments = document.payments.filter(status="POSTED")
    if exclude_payment:
        payments = payments.exclude(pk=exclude_payment)
    net = payments.aggregate(net=Sum(Case(
        When(kind="REFUND", then=-F("amount")), default=F("amount"),
    )))["net"] or Decimal("0")
    if not Decimal("0") <= net + delta <= document.total:
        raise serializers.ValidationError("El importe supera el saldo o el dinero disponible para reembolsar.")


class PaymentViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, CanAccessCompany]

    def get_queryset(self):
        queryset = Payment.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("sale", "purchase", "created_by")
        if self.request.user.is_superuser:
            return queryset
        role = Membership.objects.get(
            company_id=self.kwargs["company_id"], user=self.request.user, is_active=True,
        ).role
        if role == Membership.Role.SELLER:
            return queryset.filter(sale__isnull=False)
        if role == Membership.Role.WAREHOUSE:
            return queryset.filter(purchase__isnull=False)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        data = serializer.validated_data
        document = data.get("sale") or data["purchase"]
        document = type(document).objects.select_for_update().get(pk=document.pk)
        refund = data.get("kind", "PAYMENT") == "REFUND"
        if not refund and document.status not in ("CONFIRMED", "FULFILLED"):
            raise serializers.ValidationError("El documento debe estar confirmado para registrar un pago.")
        check_balance(document, -data["amount"] if refund else data["amount"])
        serializer.save(company_id=self.kwargs["company_id"], created_by=self.request.user)

    @transaction.atomic
    def void(self, request, *args, **kwargs):
        if not IsCompanyAdmin().has_permission(request, self):
            self.permission_denied(request)
        payment = self.get_object()
        document = payment.sale or payment.purchase
        document = type(document).objects.select_for_update().get(pk=document.pk)
        payment.refresh_from_db()
        if payment.status == "VOIDED":
            raise serializers.ValidationError("El pago ya está anulado.")
        reason = serializers.CharField(allow_blank=False).run_validation(request.data.get("reason", ""))
        check_balance(document, Decimal("0"), exclude_payment=payment.pk)
        payment.status = "VOIDED"
        payment.voided_at = timezone.now()
        payment.void_reason = reason
        payment.save(update_fields=["status", "voided_at", "void_reason", "updated_at"])
        return Response(self.get_serializer(payment).data, status=status.HTTP_200_OK)
