from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanAccessCompany, CanEditCatalog
from common.views import CompanyViewSet
from .models import Warehouse, StockBalance, StockReservation, StockMovement
from .serializers import (
    WarehouseSerializer, StockBalanceSerializer,
    StockReservationSerializer, StockMovementSerializer,
)


class WarehouseViewSet(CompanyViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, CanEditCatalog]

    def get_queryset(self):
        return Warehouse.objects.filter(company_id=self.kwargs["company_id"])


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated, CanAccessCompany]

    def get_queryset(self):
        return StockBalance.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("warehouse", "product").order_by("id")


class StockReservationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockReservationSerializer
    permission_classes = [IsAuthenticated, CanAccessCompany]

    def get_queryset(self):
        return StockReservation.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("sale_item", "warehouse").order_by("id")


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, CanAccessCompany]

    def get_queryset(self):
        return StockMovement.objects.filter(
            company_id=self.kwargs["company_id"],
        ).select_related("warehouse", "product", "created_by")
