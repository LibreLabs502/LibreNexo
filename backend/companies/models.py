from django.db import models
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default="GTQ")
    timezone = models.CharField(max_length=64, default="America/Guatemala")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        SELLER = "SELLER", "Vendedor"
        WAREHOUSE = "WAREHOUSE", "Bodeguero"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.SELLER,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="unique_company_user"),
            models.CheckConstraint(
                condition=models.Q(role__in=["ADMIN", "SELLER", "WAREHOUSE"]),
                name="membership_valid_role",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.company} ({self.role})"
