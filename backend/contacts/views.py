from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanAccessCompany
from common.views import CompanyViewSet
from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(CompanyViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, CanAccessCompany]

    def get_queryset(self):
        return Contact.objects.filter(company_id=self.kwargs["company_id"]).order_by("id")
