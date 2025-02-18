from django.contrib import admin
from .models import User, UserProfile, Shop, Item, Restock, Sale

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    ordering = ('date_joined',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'date_of_birth')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('date_of_birth',)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'owner', 'business_type', 'location', 'created_at')
    search_fields = ('shop_name', 'owner__username', 'business_type', 'location')
    list_filter = ('business_type', 'created_at')
    ordering = ('created_at',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'shop', 'quantity', 'created_at')
    search_fields = ('item_name', 'shop__shop_name')
    list_filter = ('shop', 'created_at')
    ordering = ('created_at',)

@admin.register(Restock)
class RestockAdmin(admin.ModelAdmin):
    list_display = ('item', 'shop', 'quantity', 'total_price', 'restocked_at')
    search_fields = ('item__item_name', 'shop__shop_name')
    list_filter = ('restocked_at',)
    ordering = ('restocked_at',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('item', 'shop', 'quantity', 'total_price', 'payment_method', 'sold_at')
    search_fields = ('item__item_name', 'shop__shop_name')
    list_filter = ('payment_method', 'sold_at')
    ordering = ('sold_at',)
    
