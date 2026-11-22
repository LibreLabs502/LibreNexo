from rest_framework import serializers

from companies.models import Membership
from .models import User


class MembershipSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "company", "company_name", "role"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "full_name", "is_superuser", "memberships"]
        read_only_fields = fields

    def get_memberships(self, user):
        memberships = user.memberships.filter(
            is_active=True, company__is_active=True,
        ).select_related("company").order_by("id")
        return MembershipSerializer(memberships, many=True).data
