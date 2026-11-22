from django.urls import path

from .views import WarehouseViewSet, StockBalanceViewSet, StockReservationViewSet, StockMovementViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/warehouses/",
        WarehouseViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="warehouses-list",
    ),
    path(
        "companies/<int:company_id>/warehouses/<int:pk>/",
        WarehouseViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="warehouses-detail",
    ),
    path(
        "companies/<int:company_id>/stock-balances/",
        StockBalanceViewSet.as_view({
            "get": "list",
        }),
        name="stock-balances-list",
    ),
    path(
        "companies/<int:company_id>/stock-balances/<int:pk>/",
        StockBalanceViewSet.as_view({
            "get": "retrieve",
        }),
        name="stock-balances-detail",
    ),
    path(
        "companies/<int:company_id>/stock-reservations/",
        StockReservationViewSet.as_view({
            "get": "list",
        }),
        name="stock-reservations-list",
    ),
    path(
        "companies/<int:company_id>/stock-reservations/<int:pk>/",
        StockReservationViewSet.as_view({
            "get": "retrieve",
        }),
        name="stock-reservations-detail",
    ),
    path(
        "companies/<int:company_id>/stock-movements/",
        StockMovementViewSet.as_view({
            "get": "list",
        }),
        name="stock-movements-list",
    ),
    path(
        "companies/<int:company_id>/stock-movements/<int:pk>/",
        StockMovementViewSet.as_view({
            "get": "retrieve",
        }),
        name="stock-movements-detail",
    ),
]
