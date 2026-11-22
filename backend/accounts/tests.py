from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from companies.models import Company, Membership
from .models import User
from .permissions import CanManageInventory, CanSell, IsCompanyAdmin


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Empresa uno")
        self.other = Company.objects.create(name="Empresa dos")
        self.user = User.objects.create_user(username="vendedor", password="test-password")
        self.member = Membership.objects.create(company=self.company, user=self.user)
        self.request = SimpleNamespace(user=self.user)
        self.view = SimpleNamespace(kwargs={"company_id": self.company.pk})

    def login(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username, "password": "test-password",
        })
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data

    def test_login_me_and_refresh(self):
        tokens = self.login()
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["memberships"][0]["role"], "SELLER")
        self.assertFalse(response.data["is_superuser"])
        self.assertNotIn("password", response.data)
        self.assertEqual(self.client.post(reverse("token_refresh"), {
            "refresh": tokens["refresh"],
        }).status_code, 200)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("me")).status_code, 401)

    def test_invalid_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username, "password": "incorrecta",
        })
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_login_or_use_token(self):
        self.login()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.get(reverse("me")).status_code, 401)
        self.assertEqual(self.client.post(reverse("login"), {
            "username": self.user.username, "password": "test-password",
        }).status_code, 401)

    def test_role_permissions(self):
        for role, expected in [
            ("ADMIN", [True, True, True]),
            ("SELLER", [False, True, False]),
            ("WAREHOUSE", [False, False, True]),
        ]:
            with self.subTest(role=role):
                self.member.role = role
                self.member.save()
                actual = [permission().has_permission(self.request, self.view)
                          for permission in [IsCompanyAdmin, CanSell, CanManageInventory]]
                self.assertEqual(actual, expected)

    def test_company_isolation_and_different_roles(self):
        self.view.kwargs["company_id"] = self.other.pk
        self.assertFalse(CanSell().has_permission(self.request, self.view))
        Membership.objects.create(company=self.other, user=self.user, role="WAREHOUSE")
        self.assertTrue(CanManageInventory().has_permission(self.request, self.view))
        self.assertFalse(CanSell().has_permission(self.request, self.view))

    def test_inactive_membership_and_company(self):
        self.member.is_active = False
        self.member.save()
        self.assertFalse(CanSell().has_permission(self.request, self.view))
        self.login()
        self.assertEqual(self.client.get(reverse("me")).data["memberships"], [])
        self.member.is_active = True
        self.member.save()
        self.company.is_active = False
        self.company.save()
        self.assertFalse(CanSell().has_permission(self.request, self.view))
        self.assertEqual(self.client.get(reverse("me")).data["memberships"], [])

    def test_anonymous_and_missing_company_denied(self):
        self.request.user = AnonymousUser()
        self.assertFalse(CanSell().has_permission(self.request, self.view))
        self.request.user = self.user
        self.view.kwargs = {}
        self.assertFalse(CanSell().has_permission(self.request, self.view))

    def test_superuser_access_without_membership(self):
        self.request.user = User.objects.create_superuser(username="root", password="test")
        self.view.kwargs["company_id"] = self.other.pk
        for permission in [IsCompanyAdmin(), CanSell(), CanManageInventory()]:
            self.assertTrue(permission.has_permission(self.request, self.view))
        self.request.user.is_active = False
        self.assertFalse(CanSell().has_permission(self.request, self.view))

    def test_object_must_belong_to_url_company(self):
        obj = SimpleNamespace(company_id=self.other.pk)
        self.assertFalse(CanSell().has_object_permission(self.request, self.view, obj))

    def test_roles_cannot_be_changed_through_me(self):
        self.login()
        response = self.client.patch(reverse("me"), {"is_superuser": True, "role": "ADMIN"})
        self.assertEqual(response.status_code, 405)
        self.user.refresh_from_db()
        self.member.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.member.role, "SELLER")

    def test_role_change_applies_with_existing_token(self):
        self.login()
        self.member.role = "WAREHOUSE"
        self.member.save()
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["memberships"][0]["role"], "WAREHOUSE")
        self.assertFalse(CanSell().has_permission(self.request, self.view))
        self.assertTrue(CanManageInventory().has_permission(self.request, self.view))

    def test_unknown_role_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.filter(pk=self.member.pk).update(role="SUPERUSER")
