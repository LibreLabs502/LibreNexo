from django.urls import path

from .views import QuotationViewSet, QuotationItemViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/quotations/",
        QuotationViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="quotations-list",
    ),
    path(
        "companies/<int:company_id>/quotations/<int:pk>/",
        QuotationViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="quotations-detail",
    ),
    path(
        "companies/<int:company_id>/quotation-items/",
        QuotationItemViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="quotation-items-list",
    ),
    path(
        "companies/<int:company_id>/quotation-items/<int:pk>/",
        QuotationItemViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="quotation-items-detail",
    ),
]
