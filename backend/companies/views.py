from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsCompanyAdmin
from .models import Company, Membership
from .serializers import CompanySerializer, MembershipSerializer


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Company.objects.all()
        return Company.objects.filter(
            is_active=True, memberships__user=self.request.user, memberships__is_active=True,
        ).distinct()


class MembershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get_queryset(self):
        return Membership.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("user").order_by("id")
