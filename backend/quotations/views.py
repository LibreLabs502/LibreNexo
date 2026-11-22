from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanSell
from common.views import DocumentViewSet, ItemViewSet
from .models import Quotation, QuotationItem
from .serializers import QuotationSerializer, QuotationItemSerializer


class QuotationViewSet(DocumentViewSet):
    queryset = Quotation.objects.all()
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated, CanSell]

    def get_queryset(self):
        return super().get_queryset().filter(
            company_id=self.kwargs["company_id"],
        ).select_related('customer', 'created_by').prefetch_related("items__product")


class QuotationItemViewSet(ItemViewSet):
    serializer_class = QuotationItemSerializer
    permission_classes = [IsAuthenticated, CanSell]
    parent_field = "quotation"

    def get_queryset(self):
        queryset = QuotationItem.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("quotation", "product").order_by("id")
        document_id = self.request.query_params.get("quotation")
        if document_id:
            document_id = serializers.IntegerField(min_value=1).run_validation(document_id)
            queryset = queryset.filter(quotation_id=document_id)
        return queryset
