from django.urls import path

from .views import ProductViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/products/",
        ProductViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="products-list",
    ),
    path(
        "companies/<int:company_id>/products/<int:pk>/",
        ProductViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="products-detail",
    ),
]
