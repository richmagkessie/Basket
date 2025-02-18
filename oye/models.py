from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import random
# Create your models here.


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(8, message=_("Password must be at least 8 characters long.")),
            MaxLengthValidator(100, message=_("Password must not exceed 100 characters."))
        ],
    )
    email = models.EmailField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def set_password(self, raw_password):
        """Sets the user's password, hashing it."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks the user's password."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures", blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class Shop(models.Model):
    BUSINESS_TYPE = (
        ("retail", "Retail"),
        ("wholesale", "Wholesale"),
        ("service", "Service"),
        ("manufacturing", "Manufacturing"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    shop_name = models.CharField(max_length=200, unique=True) 
    location = models.CharField(max_length=100, blank=True, null=True)
    landmark = models.CharField(max_length=100, blank=True, null=True)
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPE, default="retail")
    description = models.TextField(blank=True, null=True)
    operating_hours = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Days and times the shop is open (e.g., Mon-Fri: 9am-5pm)"
    )
    number_of_employees = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of employees in the shop"
    )
    tax_identification_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Tax Identification Number (TIN) for compliance"
    )
    bank_details = models.TextField(
        blank=True,
        null=True,
        help_text="Bank details for financial transactions like payouts"
    )
    terms_and_conditions_accepted = models.BooleanField(
        default=False,
        help_text="Indicates if the owner has agreed to the terms and conditions"
    )
    privacy_policy_accepted = models.BooleanField(
        default=False,
        help_text="Indicates if the owner has agreed to the privacy policy"
    )
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

    def total_items_quantity(self):
        return sum(item.quantity for item in self.items.all())


class Item(models.Model):
    ITEM_CATEGORIES = (
        ("grocery", "Grocery"),
        ("electronics", "Electronics"),
        ("clothing", "Clothing"),
        ("furniture", "Furniture"),
        ("appliances", "Appliances"),
        ("books", "Books"),
        ("stationery", "Stationery"),
        ("toys", "Toys"),
        ("beauty", "Beauty"),
        ("health", "Health"),
        ("pharmacy", "Pharmacy"),
        ("hardware", "Hardware"),
        ("software", "Software"),
        ("services", "Services"),
        ("other", "Other"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    category = models.CharField(max_length=100, choices=ITEM_CATEGORIES, default="other")
    item_name = models.CharField(max_length=255, help_text="Name of the Item.")
    description = models.TextField(blank=True, null=True, help_text="Description of the Item.")
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Cost price of the Item.",
        default=0.00
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Selling price of the Item.",
        default=0.00
    )
    quantity = models.IntegerField(
        default=0, 
        help_text="Stock quantity available in the shop."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def profit(self):
        """Calculate and return the profit for the item."""
        return self.selling_price - self.cost_price

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"

    def __str__(self):
        return f"{self.item_name}"


class Restock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="restocks")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="restocks")
    quantity = models.IntegerField(help_text="Quantity of items restocked.")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price of the restocked items.")
    restocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Restock of {self.quantity} {self.item.item_name} for {self.shop.shop_name} on {self.restocked_at}"

class Sale(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
        ('other', 'Other'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sales")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="sales")
    quantity = models.IntegerField(help_text="Quantity of items sold.")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price of the sold items.")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, help_text="Payment method used for the sale.")
    sold_at = models.DateTimeField(auto_now_add=True)
    customer = models.CharField(max_length=255, blank=True, null=True, help_text="Customer name")

    def __str__(self):
        return f"Sale of {self.quantity} {self.item.item_name} for {self.shop.shop_name} on {self.sold_at}"