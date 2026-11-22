from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CanEditCatalog
from common.views import CompanyViewSet
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(CompanyViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, CanEditCatalog]

    def get_queryset(self):
        return Product.objects.filter(company_id=self.kwargs["company_id"]).order_by("id")
