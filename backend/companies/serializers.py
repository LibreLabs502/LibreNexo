from rest_framework import serializers

from .models import Company, Membership


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id", "name", "legal_name", "tax_id", "phone", "address",
            "currency", "timezone", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id", "company", "user", "username",
            "role", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields
