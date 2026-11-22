from django.urls import path

from .views import PaymentViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/payments/",
        PaymentViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="payments-list",
    ),
    path(
        "companies/<int:company_id>/payments/<int:pk>/",
        PaymentViewSet.as_view({
            "get": "retrieve",
        }),
        name="payments-detail",
    ),
    path(
        "companies/<int:company_id>/payments/<int:pk>/void/",
        PaymentViewSet.as_view({
            "post": "void",
        }),
        name="payments-void",
    ),
]
