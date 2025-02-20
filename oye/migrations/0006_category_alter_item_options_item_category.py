# Generated by Django 4.2.6 on 2025-01-29 02:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("oye", "0005_alter_item_options_alter_item_description_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(help_text="Name of the Category.", max_length=255),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="Description of the Category.", null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Category",
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.AlterModelOptions(
            name="item",
            options={"verbose_name": "Item", "verbose_name_plural": "Items"},
        ),
        migrations.AddField(
            model_name="item",
            name="category",
            field=models.ForeignKey(
                blank=True,
                help_text="Category of the Item.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="items",
                to="oye.category",
            ),
        ),
    ]
