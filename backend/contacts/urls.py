from django.urls import path

from .views import ContactViewSet


urlpatterns = [
    path(
        "companies/<int:company_id>/contacts/",
        ContactViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="contacts-list",
    ),
    path(
        "companies/<int:company_id>/contacts/<int:pk>/",
        ContactViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="contacts-detail",
    ),
]
