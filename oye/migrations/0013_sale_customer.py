# Generated by Django 4.2.6 on 2025-02-09 01:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oye", "0012_remove_shop_business_registration_certificate_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sale",
            name="customer",
            field=models.CharField(
                blank=True, help_text="Customer name", max_length=255, null=True
            ),
        ),
    ]
