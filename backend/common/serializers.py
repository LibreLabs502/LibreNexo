from copy import copy
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from companies.models import Company


class CompanySerializer(serializers.ModelSerializer):
    """Valida las relaciones y restricciones dentro de la empresa de la URL."""

    def get_fields(self):
        fields = super().get_fields()
        company_id = self.context["view"].kwargs["company_id"]
        for field in fields.values():
            if isinstance(field, serializers.PrimaryKeyRelatedField) and field.queryset is not None:
                if hasattr(field.queryset.model, "company_id"):
                    field.queryset = field.queryset.filter(company_id=company_id)
        return fields

    def validate(self, attrs):
        company = get_object_or_404(Company, pk=self.context["view"].kwargs["company_id"])
        instance = copy(self.instance) if self.instance else self.Meta.model()
        instance.company = company
        for name, value in attrs.items():
            setattr(instance, name, value)
        # created_by y las fechas automáticas se asignan al guardar.
        exclude = ["created_at", "updated_at"]
        if hasattr(instance, "created_by_id") and not instance.created_by_id:
            exclude.append("created_by")
        try:
            instance.full_clean(exclude=exclude)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs


class DocumentSerializer(CompanySerializer):
    def validate(self, attrs):
        if self.instance and self.instance.status != "DRAFT":
            raise serializers.ValidationError("Solo se pueden editar documentos en borrador.")
        if "items" in self.initial_data:
            raise serializers.ValidationError({"items": "Agregá las líneas desde el endpoint de detalles."})
        return super().validate(attrs)


class ItemSerializer(CompanySerializer):
    parent_field = None
    price_field = "unit_price"

    def validate(self, attrs):
        parent = attrs.get(self.parent_field, getattr(self.instance, self.parent_field, None))
        if self.instance and self.parent_field in attrs:
            if parent.pk != getattr(self.instance, self.parent_field + "_id"):
                raise serializers.ValidationError({self.parent_field: "No se puede cambiar el documento de una línea."})
        if parent.status != "DRAFT":
            raise serializers.ValidationError("Solo se pueden editar líneas de documentos en borrador.")
        product = attrs.get("product", getattr(self.instance, "product", None))
        if not product.is_active:
            raise serializers.ValidationError({"product": "El producto está inactivo."})
        if not self.instance or product.pk != self.instance.product_id:
            attrs.setdefault("description", product.name)
            if self.price_field == "unit_price":
                attrs.setdefault("unit_price", product.sale_price)
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        price = attrs.get(self.price_field, getattr(self.instance, self.price_field, None))
        attrs["line_total"] = (quantity * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return super().validate(attrs)
