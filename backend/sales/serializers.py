from rest_framework import serializers

from common.serializers import DocumentSerializer, ItemSerializer
from .models import Sale, SaleItem


class SaleItemSerializer(ItemSerializer):
    parent_field = "sale"
    price_field = "unit_price"

    class Meta:
        model = SaleItem
        fields = [
            "id", "company", "sale", "product",
            "description", "quantity", "unit_price", "line_total",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "company", "line_total", "created_at", "updated_at"]
        validators = []
        extra_kwargs = {"description": {"required": False}, "unit_price": {"required": False}}


class SaleSerializer(DocumentSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id", "company", "customer", "quotation",
            "warehouse", "number", "kind", "status",
            "sold_at", "scheduled_for", "delivery_address", "terms",
            "notes", "total", "created_by", "confirmed_at",
            "fulfilled_at", "cancelled_at", "cancellation_reason", "items",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "company", "status", "total",
            "created_by", "created_at", "updated_at", "confirmed_at",
            "fulfilled_at", "cancelled_at", "cancellation_reason",
        ]
        validators = []

    def validate_customer(self, contact):
        if contact and (not contact.is_customer or not contact.is_active):
            raise serializers.ValidationError("El contacto no está activo o no tiene el rol necesario.")
        return contact

    def validate_warehouse(self, warehouse):
        if not warehouse.is_active:
            raise serializers.ValidationError("La bodega está inactiva.")
        return warehouse
