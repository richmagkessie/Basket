# Generated by Django 4.2.6 on 2025-01-29 06:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("oye", "0010_item_cost_price_item_selling_price"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="item",
            name="price",
        ),
    ]
