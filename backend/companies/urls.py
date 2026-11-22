from django.urls import path

from .views import CompanyViewSet, MembershipViewSet


urlpatterns = [
    path(
        "companies/",
        CompanyViewSet.as_view({
            "get": "list",
        }),
        name="companies-list",
    ),
    path(
        "companies/<int:pk>/",
        CompanyViewSet.as_view({
            "get": "retrieve",
        }),
        name="companies-detail",
    ),
    path(
        "companies/<int:company_id>/memberships/",
        MembershipViewSet.as_view({
            "get": "list",
        }),
        name="memberships-list",
    ),
    path(
        "companies/<int:company_id>/memberships/<int:pk>/",
        MembershipViewSet.as_view({
            "get": "retrieve",
        }),
        name="memberships-detail",
    ),
]
