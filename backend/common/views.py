from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets


class CompanyViewSet(viewsets.ModelViewSet):
    """La empresa viene de la URL, nunca del formulario."""

    def perform_create(self, serializer):
        serializer.save(company_id=self.kwargs["company_id"])

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError as exc:
            raise serializers.ValidationError("El registro está duplicado o incumple una restricción.") from exc

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().update(request, *args, **kwargs)
        except IntegrityError as exc:
            raise serializers.ValidationError("El registro está duplicado o incumple una restricción.") from exc

    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().destroy(request, *args, **kwargs)
        except ProtectedError as exc:
            raise serializers.ValidationError("Este registro tiene operaciones asociadas. Desactivalo en lugar de eliminarlo.") from exc


class DocumentViewSet(CompanyViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ("update", "partial_update", "destroy"):
            queryset = queryset.select_for_update(of=("self",))
        return queryset

    def perform_create(self, serializer):
        serializer.save(company_id=self.kwargs["company_id"], created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != "DRAFT":
            raise serializers.ValidationError("Solo se pueden eliminar documentos en borrador.")
        instance.delete()


class ItemViewSet(CompanyViewSet):
    parent_field = None

    def lock_parent(self, parent):
        parent = get_object_or_404(type(parent).objects.select_for_update(), pk=parent.pk)
        if parent.status != "DRAFT":
            raise serializers.ValidationError("Solo se pueden modificar documentos en borrador.")
        return parent

    def update_total(self, parent):
        total = parent.items.aggregate(total=Sum("line_total"))["total"] or Decimal("0")
        parent.total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        try:
            parent._meta.get_field("total").clean(parent.total, parent)
        except ModelValidationError as exc:
            raise serializers.ValidationError({"total": exc.messages}) from exc
        parent.save(update_fields=["total", "updated_at"])

    def perform_create(self, serializer):
        parent = self.lock_parent(serializer.validated_data[self.parent_field])
        serializer.save(company_id=self.kwargs["company_id"])
        self.update_total(parent)

    def perform_update(self, serializer):
        parent = self.lock_parent(getattr(serializer.instance, self.parent_field))
        # Otra solicitud pudo cambiar la línea antes de tomar el bloqueo.
        serializer.instance = get_object_or_404(type(serializer.instance), pk=serializer.instance.pk)
        serializer.validated_data.update(serializer.validate(serializer.validated_data))
        serializer.save()
        self.update_total(parent)

    def perform_destroy(self, instance):
        parent = self.lock_parent(getattr(instance, self.parent_field))
        instance.delete()
        self.update_total(parent)
