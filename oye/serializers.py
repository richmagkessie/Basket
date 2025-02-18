from rest_framework import serializers
from .models import User, UserProfile, Shop, Item, Restock, Sale


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirmation = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirmation']

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        # Remove password_confirmation from validated data before creating the user
        validated_data.pop('password_confirmation')
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Hash the password before saving
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'phone_number', 'address', 'date_of_birth']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']

class UserAccountUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = instance.userprofile

        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        # Update UserProfile fields
        profile.bio = profile_data.get('bio', profile.bio)
        profile.profile_picture = profile_data.get('profile_picture', profile.profile_picture)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.address = profile_data.get('address', profile.address)
        profile.date_of_birth = profile_data.get('date_of_birth', profile.date_of_birth)
        profile.save()

        return instance
    
        
# Password Reset
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=5)
    confirm_password = serializers.CharField(write_only=True, min_length=5)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class ShopSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Shop
        fields = [
            'id', 'shop_name', 'owner', 'location', 'landmark', 'business_type',
            'description', 'operating_hours', 'number_of_employees',
             'tax_identification_number',
            'bank_details', 'terms_and_conditions_accepted', 'privacy_policy_accepted',
            'created_at', 'updated_at'
        ]
    

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'shop', 'item_name', 'category',
                  'description', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'shop']
        

class RestockSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    class Meta:
        model = Restock
        fields = ['id', 'item', 'quantity', 'total_price', 'restocked_at']
        read_only_fields = ['id', 'item', 'restocked_at']
        

# class SaleSerializer(serializers.ModelSerializer):
#     item = ItemSerializer(read_only=True)
#     class Meta:
#         model = Sale
#         fields = ['id', 'shop', 'item', 'quantity', 'total_price', 'payment_method', 'sold_at', 'cost_price', 'profit']
#         read_only_fields = ['id', 'shop', 'item', 'total_price', 'sold_at', 'cost_price']

class SaleSerializer(serializers.ModelSerializer):
    profit = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ['id', 'shop', 'item', 'quantity', 'total_price', 'cost_price', 'profit', 'payment_method', 'sold_at']
        read_only_fields = ['id', 'shop', 'item', 'total_price', 'cost_price', 'profit', 'sold_at']

    def get_profit(self, obj):
        return obj.total_price - obj.cost_price
    

class InventoryAnalysisSerializer(serializers.Serializer):
    total_items = serializers.IntegerField()
    total_restocked = serializers.IntegerField()
    total_sold = serializers.IntegerField()
    total_profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    items_to_restock = serializers.IntegerField()
    most_bought_item = serializers.DictField(child=serializers.CharField())
    least_bought_item = serializers.DictField(child=serializers.CharField())