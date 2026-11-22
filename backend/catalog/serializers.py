from rest_framework import serializers

from common.serializers import CompanySerializer
from .models import Product


class ProductSerializer(CompanySerializer):
    class Meta:
        model = Product
        fields = [
            "id", "company", "sku", "name",
            "description", "kind", "unit", "sale_price",
            "minimum_stock", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']
        validators = []
