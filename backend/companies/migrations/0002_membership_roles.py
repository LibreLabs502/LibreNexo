from django.db import migrations, models


def migrate_roles(apps, schema_editor):
    Membership = apps.get_model("companies", "Membership")
    memberships = Membership.objects.using(schema_editor.connection.alias)
    memberships.filter(role="OWNER").update(role="ADMIN")
    memberships.filter(role="OPERATOR").update(role="SELLER")


def restore_roles(apps, schema_editor):
    Membership = apps.get_model("companies", "Membership")
    memberships = Membership.objects.using(schema_editor.connection.alias)
    memberships.filter(role__in=["SELLER", "WAREHOUSE"]).update(role="OPERATOR")


class Migration(migrations.Migration):
    dependencies = [("companies", "0001_initial")]

    operations = [
        migrations.RunPython(migrate_roles, restore_roles),
        migrations.AlterField(
            model_name="membership",
            name="role",
            field=models.CharField(
                choices=[("ADMIN", "Administrador"), ("SELLER", "Vendedor"), ("WAREHOUSE", "Bodeguero")],
                default="SELLER",
                max_length=10,
            ),
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.CheckConstraint(
                condition=models.Q(role__in=["ADMIN", "SELLER", "WAREHOUSE"]),
                name="membership_valid_role",
            ),
        ),
    ]
