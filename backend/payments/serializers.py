from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from accounts.permissions import CanManageInventory, CanSell, IsCompanyAdmin
from common.serializers import CompanySerializer
from .models import Payment


class PaymentSerializer(CompanySerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "company", "sale", "purchase", "direction", "kind", "amount",
            "method", "reference", "paid_at", "status", "notes", "created_by",
            "voided_at", "void_reason", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "company", "direction", "status", "created_by",
            "voided_at", "void_reason", "created_at", "updated_at",
        ]
        validators = []

    def validate(self, attrs):
        sale, purchase = attrs.get("sale"), attrs.get("purchase")
        if bool(sale) == bool(purchase):
            raise serializers.ValidationError("Asociá el pago a una venta o una compra, nunca a ambas.")
        request, view = self.context["request"], self.context["view"]
        permission = CanSell() if sale else CanManageInventory()
        if not permission.has_permission(request, view):
            raise PermissionDenied("No tenés permiso para registrar este pago.")
        refund = attrs.get("kind", "PAYMENT") == "REFUND"
        if refund and not IsCompanyAdmin().has_permission(request, view):
            raise PermissionDenied("Solo el administrador puede registrar reembolsos.")
        attrs["direction"] = "IN" if bool(sale) != refund else "OUT"
        return super().validate(attrs)
