from rest_framework import serializers

from common.serializers import CompanySerializer
from .models import Warehouse, StockBalance, StockReservation, StockMovement


class WarehouseSerializer(CompanySerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'company', 'name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']
        validators = []


class StockBalanceSerializer(CompanySerializer):
    quantity_available = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = StockBalance
        fields = [
            "id", "company", "warehouse", "product",
            "quantity_on_hand", "quantity_reserved", "quantity_available", "created_at",
            "updated_at",
        ]
        read_only_fields = fields
        validators = []


class StockReservationSerializer(CompanySerializer):
    class Meta:
        model = StockReservation
        fields = [
            "id", "company", "sale_item", "warehouse",
            "quantity", "status", "created_at", "updated_at",
        ]
        read_only_fields = fields
        validators = []


class StockMovementSerializer(CompanySerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id", "company", "warehouse", "product",
            "quantity_delta", "kind", "purchase_item", "sale_item",
            "reverses", "reason", "created_by", "occurred_at",
            "created_at", "updated_at",
        ]
        read_only_fields = fields
        validators = []
