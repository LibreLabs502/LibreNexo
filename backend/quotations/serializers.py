from rest_framework import serializers

from common.serializers import DocumentSerializer, ItemSerializer
from .models import Quotation, QuotationItem


class QuotationItemSerializer(ItemSerializer):
    parent_field = "quotation"
    price_field = "unit_price"

    class Meta:
        model = QuotationItem
        fields = [
            "id", "company", "quotation", "product",
            "description", "quantity", "unit_price", "line_total",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "company", "line_total", "created_at", "updated_at"]
        validators = []
        extra_kwargs = {"description": {"required": False}, "unit_price": {"required": False}}


class QuotationSerializer(DocumentSerializer):
    items = QuotationItemSerializer(many=True, read_only=True)

    class Meta:
        model = Quotation
        fields = [
            "id", "company", "customer", "number",
            "status", "issued_at", "valid_until", "terms",
            "notes", "total", "created_by", "items",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "company", "status", "total",
            "created_by", "created_at", "updated_at",
        ]
        validators = []

    def validate_customer(self, contact):
        if contact and (not contact.is_customer or not contact.is_active):
            raise serializers.ValidationError("El contacto no está activo o no tiene el rol necesario.")
        return contact
