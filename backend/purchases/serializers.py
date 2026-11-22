from rest_framework import serializers

from common.serializers import DocumentSerializer, ItemSerializer
from .models import Purchase, PurchaseItem


class PurchaseItemSerializer(ItemSerializer):
    parent_field = "purchase"
    price_field = "unit_cost"

    class Meta:
        model = PurchaseItem
        fields = [
            "id", "company", "purchase", "product",
            "description", "quantity", "unit_cost", "line_total",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "company", "line_total", "created_at", "updated_at"]
        validators = []
        extra_kwargs = {"description": {"required": False}}


class PurchaseSerializer(DocumentSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = [
            "id", "company", "supplier", "warehouse",
            "number", "supplier_reference", "purchased_at", "status",
            "total", "notes", "created_by", "confirmed_at",
            "cancelled_at", "cancellation_reason", "items", "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "company", "status", "total",
            "created_by", "created_at", "updated_at", "confirmed_at",
            "cancelled_at", "cancellation_reason",
        ]
        validators = []

    def validate_supplier(self, contact):
        if contact and (not contact.is_supplier or not contact.is_active):
            raise serializers.ValidationError("El contacto no está activo o no tiene el rol necesario.")
        return contact

    def validate_warehouse(self, warehouse):
        if not warehouse.is_active:
            raise serializers.ValidationError("La bodega está inactiva.")
        return warehouse
