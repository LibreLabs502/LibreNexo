from django.urls import path

from .views import PurchaseViewSet, PurchaseItemViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/purchases/",
        PurchaseViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="purchases-list",
    ),
    path(
        "companies/<int:company_id>/purchases/<int:pk>/",
        PurchaseViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="purchases-detail",
    ),
    path(
        "companies/<int:company_id>/purchase-items/",
        PurchaseItemViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="purchase-items-list",
    ),
    path(
        "companies/<int:company_id>/purchase-items/<int:pk>/",
        PurchaseItemViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="purchase-items-detail",
    ),
]
