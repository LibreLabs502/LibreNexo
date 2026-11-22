from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanSell
from common.views import DocumentViewSet, ItemViewSet
from .models import Sale, SaleItem
from .serializers import SaleSerializer, SaleItemSerializer


class SaleViewSet(DocumentViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated, CanSell]

    def get_queryset(self):
        return super().get_queryset().filter(
            company_id=self.kwargs["company_id"],
        ).select_related('customer', 'quotation', 'warehouse', 'created_by').prefetch_related("items__product")


class SaleItemViewSet(ItemViewSet):
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated, CanSell]
    parent_field = "sale"

    def get_queryset(self):
        queryset = SaleItem.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("sale", "product").order_by("id")
        document_id = self.request.query_params.get("sale")
        if document_id:
            document_id = serializers.IntegerField(min_value=1).run_validation(document_id)
            queryset = queryset.filter(sale_id=document_id)
        return queryset
