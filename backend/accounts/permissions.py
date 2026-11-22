from rest_framework.permissions import BasePermission

from companies.models import Membership


class CompanyRolePermission(BasePermission):
    """Las vistas de empresa deben recibir company_id en su URL.

    El permiso valida acceso; cada vista también debe filtrar su queryset por
    company_id para no listar registros de otras empresas.
    """

    allowed_roles = ()
    message = "No tenés permisos para realizar esta acción en esta empresa."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser:
            return True

        company_id = view.kwargs.get("company_id")
        if company_id is None:
            return False

        return Membership.objects.filter(
            company_id=company_id,
            company__is_active=True,
            user=user,
            is_active=True,
            role__in=self.allowed_roles,
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Ni siquiera un superusuario debe mezclar un objeto con otra URL.
        company_id = view.kwargs.get("company_id")
        if company_id is None or str(getattr(obj, "company_id", None)) != str(company_id):
            return False
        return self.has_permission(request, view)


class IsCompanyAdmin(CompanyRolePermission):
    allowed_roles = (Membership.Role.ADMIN,)


class CanSell(CompanyRolePermission):
    allowed_roles = (Membership.Role.ADMIN, Membership.Role.SELLER)


class CanManageInventory(CompanyRolePermission):
    allowed_roles = (Membership.Role.ADMIN, Membership.Role.WAREHOUSE)


class CanAccessCompany(CompanyRolePermission):
    allowed_roles = tuple(Membership.Role.values)


class CanEditCatalog(CanManageInventory):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return CanAccessCompany().has_permission(request, view)
        return super().has_permission(request, view)
