from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanManageInventory
from common.views import DocumentViewSet, ItemViewSet
from .models import Purchase, PurchaseItem
from .serializers import PurchaseSerializer, PurchaseItemSerializer


class PurchaseViewSet(DocumentViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated, CanManageInventory]

    def get_queryset(self):
        return super().get_queryset().filter(
            company_id=self.kwargs["company_id"],
        ).select_related('supplier', 'warehouse', 'created_by').prefetch_related("items__product")


class PurchaseItemViewSet(ItemViewSet):
    serializer_class = PurchaseItemSerializer
    permission_classes = [IsAuthenticated, CanManageInventory]
    parent_field = "purchase"

    def get_queryset(self):
        queryset = PurchaseItem.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("purchase", "product").order_by("id")
        document_id = self.request.query_params.get("purchase")
        if document_id:
            document_id = serializers.IntegerField(min_value=1).run_validation(document_id)
            queryset = queryset.filter(purchase_id=document_id)
        return queryset
