from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Product
from companies.models import Company, Membership
from contacts.models import Contact
from inventory.models import Warehouse, StockBalance
from payments.models import Payment
from purchases.models import Purchase
from sales.models import Sale, SaleItem


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BusinessAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="admin", password="test")
        self.company = Company.objects.create(name="Empresa")
        self.other = Company.objects.create(name="Otra")
        self.member = Membership.objects.create(company=self.company, user=self.user, role="ADMIN")
        self.client.force_authenticate(self.user)
        self.customer = Contact.objects.create(company=self.company, name="Cliente", is_supplier=True)
        self.warehouse = Warehouse.objects.create(company=self.company, name="Principal")
        self.product = Product.objects.create(company=self.company, sku="P1", name="Producto", sale_price=10)
        self.sale = Sale.objects.create(
            company=self.company, warehouse=self.warehouse, number="V1", created_by=self.user,
        )

    def url(self, resource, pk=None, company=None):
        return reverse(resource + ("-detail" if pk else "-list"), kwargs={
            "company_id": (company or self.company).pk, **({"pk": pk} if pk else {}),
        })

    def role(self, role):
        self.member.role = role
        self.member.save()

    def test_all_list_endpoints(self):
        resources = [
            "contacts", "products", "warehouses", "stock-balances", "stock-reservations",
            "stock-movements", "quotations", "quotation-items", "purchases", "purchase-items",
            "sales", "sale-items", "payments", "memberships",
        ]
        for resource in resources:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get(self.url(resource)).status_code, 200)

    def test_company_lists_are_scoped(self):
        response = self.client.get(reverse("companies-list"))
        self.assertEqual([item["id"] for item in response.data], [self.company.pk])
        self.assertEqual(self.client.get(reverse("companies-detail", kwargs={"pk": self.other.pk})).status_code, 404)

    def test_company_access_and_object_isolation(self):
        self.assertEqual(self.client.get(self.url("products", company=self.other)).status_code, 403)
        product = Product.objects.create(company=self.other, sku="P1", name="Ajeno")
        self.assertEqual(self.client.get(self.url("products", product.pk)).status_code, 404)
        self.member.is_active = False
        self.member.save()
        self.assertEqual(self.client.post(self.url("contacts"), {"name": "Intruso"}).status_code, 403)

    def test_product_unique_and_company_cannot_be_spoofed(self):
        data = {"sku": "P2", "name": "Nuevo", "company": self.other.pk}
        response = self.client.post(self.url("products"), data)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["company"], self.company.pk)
        self.assertEqual(self.client.post(self.url("products"), data).status_code, 400)
        data["sku"] = "P3"
        data["sale_price"] = "-1"
        self.assertEqual(self.client.post(self.url("products"), data).status_code, 400)

    def test_role_boundaries(self):
        self.role("SELLER")
        self.assertEqual(self.client.get(self.url("products")).status_code, 200)
        self.assertEqual(self.client.post(self.url("products"), {"sku": "x", "name": "x"}).status_code, 403)
        self.assertEqual(self.client.get(self.url("purchases")).status_code, 403)
        self.assertEqual(self.client.get(self.url("sales")).status_code, 200)
        self.assertEqual(self.client.get(self.url("memberships")).status_code, 403)
        self.role("WAREHOUSE")
        self.assertEqual(self.client.get(self.url("sales")).status_code, 403)
        self.assertEqual(self.client.get(self.url("purchases")).status_code, 200)

    def test_cross_company_foreign_keys(self):
        other_warehouse = Warehouse.objects.create(company=self.other, name="Ajena")
        response = self.client.post(self.url("sales"), {"number": "V2", "warehouse": other_warehouse.pk})
        self.assertEqual(response.status_code, 400)
        other_product = Product.objects.create(company=self.other, sku="P2", name="Ajeno")
        response = self.client.post(self.url("sale-items"), {
            "sale": self.sale.pk, "product": other_product.pk, "quantity": 1,
        })
        self.assertEqual(response.status_code, 400)

    def test_sale_item_totals_and_history(self):
        response = self.client.post(self.url("sale-items"), {
            "sale": self.sale.pk, "product": self.product.pk,
            "quantity": "2.125", "unit_price": "3.50", "line_total": "999",
        })
        self.assertEqual(response.status_code, 201, response.data)
        item_id = response.data["id"]
        self.assertEqual(response.data["line_total"], "7.44")
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.total, Decimal("7.44"))
        self.product.name = "Modificado"
        self.product.sale_price = 999
        self.product.save()
        response = self.client.patch(self.url("sale-items", item_id), {"quantity": "3"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["description"], "Producto")
        self.assertEqual(response.data["unit_price"], "3.50")
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.total, Decimal("10.50"))
        self.assertEqual(self.client.delete(self.url("sale-items", item_id)).status_code, 204)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.total, 0)

    def test_documents_and_lines_for_each_module(self):
        for documents, lines, parent, extra in [
            ("sales", "sale-items", "sale", {"warehouse": self.warehouse.pk}),
            ("purchases", "purchase-items", "purchase", {"warehouse": self.warehouse.pk, "supplier": self.customer.pk}),
            ("quotations", "quotation-items", "quotation", {"customer": self.customer.pk}),
        ]:
            with self.subTest(module=documents):
                response = self.client.post(self.url(documents), {"number": "N1", **extra})
                self.assertEqual(response.status_code, 201, response.data)
                document_id = response.data["id"]
                data = {parent: document_id, "product": self.product.pk, "quantity": 2}
                if parent == "purchase":
                    data["unit_cost"] = "4.00"
                response = self.client.post(self.url(lines), data)
                self.assertEqual(response.status_code, 201, response.data)
                response = self.client.get(self.url(documents, document_id))
                self.assertEqual(len(response.data["items"]), 1)
                self.assertEqual(response.data["total"], "8.00" if parent == "purchase" else "20.00")

    def test_protected_records_and_draft_states(self):
        item = SaleItem.objects.create(company=self.company, sale=self.sale, product=self.product,
                                       description="Producto", quantity=1, unit_price=10, line_total=10)
        self.assertEqual(self.client.delete(self.url("products", self.product.pk)).status_code, 400)
        self.sale.status = "CONFIRMED"
        self.sale.save()
        self.assertEqual(self.client.patch(self.url("sales", self.sale.pk), {"number": "cambio"}).status_code, 400)
        self.assertEqual(self.client.delete(self.url("sales", self.sale.pk)).status_code, 400)
        self.assertEqual(self.client.patch(self.url("sale-items", item.pk), {"quantity": 2}).status_code, 400)
        self.assertEqual(self.client.delete(self.url("sale-items", item.pk)).status_code, 400)

    def test_stock_endpoints_read_only(self):
        balance = StockBalance.objects.create(company=self.company, warehouse=self.warehouse,
                                              product=self.product, quantity_on_hand=10, quantity_reserved=2)
        response = self.client.get(self.url("stock-balances", balance.pk))
        self.assertEqual(response.data["quantity_available"], "8.000")
        for resource in ["stock-balances", "stock-reservations", "stock-movements"]:
            self.assertEqual(self.client.post(self.url(resource), {}).status_code, 405)

    def test_payments_balances_refunds_and_void(self):
        self.sale.status, self.sale.total = "CONFIRMED", 100
        self.sale.save()
        data = {"sale": self.sale.pk, "amount": "60", "method": "CASH"}
        response = self.client.post(self.url("payments"), data)
        self.assertEqual(response.status_code, 201, response.data)
        payment_id = response.data["id"]
        self.assertEqual(response.data["direction"], "IN")
        self.assertEqual(self.client.post(self.url("payments"), {**data, "amount": "41"}).status_code, 400)
        self.role("SELLER")
        self.assertEqual(self.client.post(self.url("payments"), {**data, "kind": "REFUND"}).status_code, 403)
        self.role("ADMIN")
        response = self.client.post(self.url("payments"), {**data, "amount": "20", "kind": "REFUND"})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["direction"], "OUT")
        url = reverse("payments-void", kwargs={"company_id": self.company.pk, "pk": payment_id})
        # No se puede anular el cobro mientras quede un reembolso sin respaldo.
        self.assertEqual(self.client.post(url, {"reason": "Error"}).status_code, 400)
        refund_url = reverse("payments-void", kwargs={"company_id": self.company.pk, "pk": response.data["id"]})
        self.assertEqual(self.client.post(refund_url, {"reason": "Error"}).status_code, 200)
        self.assertEqual(self.client.post(url, {"reason": "Error"}).status_code, 200)
        self.assertEqual(self.client.post(url, {"reason": "Error"}).status_code, 400)

    def test_payments_scope_and_validation(self):
        self.sale.status, self.sale.total = "CONFIRMED", 100
        self.sale.save()
        purchase = Purchase.objects.create(company=self.company, supplier=self.customer,
            warehouse=self.warehouse, number="C1", total=100, status="CONFIRMED", created_by=self.user)
        for document in [{"sale": self.sale}, {"purchase": purchase}]:
            Payment.objects.create(company=self.company, created_by=self.user, amount=10, method="CASH",
                direction="IN" if "sale" in document else "OUT", **document)
        self.role("SELLER")
        response = self.client.get(self.url("payments"))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["sale"], self.sale.pk)
        response = self.client.post(self.url("payments"), {"purchase": purchase.pk, "amount": 1, "method": "CASH"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(self.url("payments"), {"amount": 1, "method": "CASH"}).status_code, 400)
        self.role("WAREHOUSE")
        response = self.client.get(self.url("payments"))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["purchase"], purchase.pk)

    def test_anonymous_and_superuser(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url("products")).status_code, 401)
        root = User.objects.create_superuser(username="root", password="test")
        self.client.force_authenticate(root)
        self.assertEqual(self.client.get(self.url("products", company=self.other)).status_code, 200)

    def test_invalid_filters_and_parent_changes(self):
        self.assertEqual(self.client.get(self.url("sale-items"), {"sale": "abc"}).status_code, 400)
        item = SaleItem.objects.create(company=self.company, sale=self.sale, product=self.product,
            description="Producto", quantity=1, unit_price=10, line_total=10)
        other_sale = Sale.objects.create(company=self.company, warehouse=self.warehouse,
            number="V2", created_by=self.user)
        self.assertEqual(self.client.patch(self.url("sale-items", item.pk), {"sale": other_sale.pk}).status_code, 400)
        for quantity in ["0", "-1"]:
            self.assertEqual(self.client.patch(self.url("sale-items", item.pk), {"quantity": quantity}).status_code, 400)

    def test_draft_payments_and_cross_company_documents_rejected(self):
        data = {"sale": self.sale.pk, "amount": "1", "method": "CASH"}
        self.assertEqual(self.client.post(self.url("payments"), data).status_code, 400)
        warehouse = Warehouse.objects.create(company=self.other, name="Otra")
        sale = Sale.objects.create(company=self.other, warehouse=warehouse, number="V1",
            total=100, status="CONFIRMED", created_by=self.user)
        self.assertEqual(self.client.post(self.url("payments"), {**data, "sale": sale.pk}).status_code, 400)

    def test_document_state_and_authorship_cannot_be_spoofed(self):
        response = self.client.post(self.url("sales"), {
            "number": "V2", "warehouse": self.warehouse.pk, "status": "FULFILLED",
            "total": "1000", "created_by": 999,
        })
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], "DRAFT")
        self.assertEqual(response.data["total"], "0.00")
        self.assertEqual(response.data["created_by"], self.user.pk)
