from rest_framework import serializers

from common.serializers import CompanySerializer
from .models import Contact


class ContactSerializer(CompanySerializer):
    def validate(self, attrs):
        customer = attrs.get("is_customer", getattr(self.instance, "is_customer", True))
        supplier = attrs.get("is_supplier", getattr(self.instance, "is_supplier", False))
        if not customer and not supplier:
            raise serializers.ValidationError("El contacto debe ser cliente, proveedor o ambos.")
        return super().validate(attrs)

    class Meta:
        model = Contact
        fields = [
            "id", "company", "name", "tax_id",
            "email", "phone", "address", "is_customer",
            "is_supplier", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']
        validators = []
