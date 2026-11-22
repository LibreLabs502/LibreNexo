from django.urls import path

from .views import SaleViewSet, SaleItemViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/sales/",
        SaleViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="sales-list",
    ),
    path(
        "companies/<int:company_id>/sales/<int:pk>/",
        SaleViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="sales-detail",
    ),
    path(
        "companies/<int:company_id>/sale-items/",
        SaleItemViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="sale-items-list",
    ),
    path(
        "companies/<int:company_id>/sale-items/<int:pk>/",
        SaleItemViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="sale-items-detail",
    ),
]
