from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework import generics    
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.views.decorators.csrf import csrf_exempt
import re
import json
from django.http import JsonResponse




from .serializers import (UserRegistrationSerializer, ShopSerializer, UserListSerializer, ItemSerializer,
                          RestockSerializer, SaleSerializer, InventoryAnalysisSerializer,
                          PasswordResetSerializer, UserAccountUpdateSerializer, UserProfileSerializer)

from .models import User, Shop, UserProfile, Item, Restock, Sale


from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from .utils import password_reset_token
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework import viewsets
from django.core.mail import send_mail


class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_id": user.id
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = User.objects.filter(username=username).first()

    if user and user.check_password(password):
        return Response(
            {'message': 'Login successful', 
             'user_id': user.id, 
             'username': username, 
             'first_name': user.first_name,
             'last_name': user.last_name}, 
            status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserAccountUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAccountUpdateSerializer

    def get_object(self):
        user_id = self.kwargs.get('pk')
        user = User.objects.get(pk=user_id)
        if user != self.request.user:
            raise PermissionDenied("You do not have permission to update this user.")
        return user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate password reset token
        token = password_reset_token.make_token(user)

        # Build password reset URL
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f'http://127.0.0.1:8000/reset-password/{uid}/{token}/'

        # Send password reset email
        subject = 'Password Reset Request'
        message = f'Hi {user.email},\n\nPlease click the following link to reset your password:\n{reset_url}'
        send_mail(subject, message, 'richmond.kessie@kintampo-hrc.org', [email])

        return Response({'message': 'Password reset email has been sent.'}, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer  # Define the serializer class

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Register.DoesNotExist):
            user = None
        
        if user is not None and password_reset_token.check_token(user, token):
            serializer = self.serializer_class(data=request.data)  # Use serializer_class attribute
            if serializer.is_valid():
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password has been reset'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Invalid token or user'}, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    lookup_field = 'pk'


class ShopUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

    def get_object(self):
        shop_id = self.kwargs.get('pk')
        user_id = self.kwargs.get('user_id')
        shop = Shop.objects.get(pk=shop_id)
        user = User.objects.get(pk=user_id)
        if shop.owner != user:
            raise PermissionDenied("You do not have permission to update this shop.")
        return shop
    
class ShopListView(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class RegisterShopView(APIView):
    def post(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=user)  # Set the owner to the user specified in the URL
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserShopsListView(generics.ListAPIView):
    serializer_class = ShopSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Shop.objects.filter(owner_id=user_id)

class UserProfileDetailView(generics.RetrieveAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user_id'


class ItemCreateView(generics.CreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def perform_create(self, serializer):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise PermissionDenied("User does not exist.")

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if shop.owner != user:
            raise PermissionDenied("You do not have permission to add items to this shop.")

        serializer.save(shop=shop)
    
class ShopItemsListView(generics.ListAPIView):
    serializer_class = ItemSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        # Debugging statements
        print(f"Shop owner ID: {shop.owner.id} (type: {type(shop.owner.id)})")
        print(f"User ID from URL: {user_id} (type: {type(user_id)})")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view items for this shop.")

        return Item.objects.filter(shop=shop)
    
class ShopItemDetailView(generics.RetrieveAPIView):
    serializer_class = ItemSerializer
    lookup_field = 'item_id'

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view items for this shop.")

        return Item.objects.filter(shop=shop)
    
    
    
class RestockCreateView(generics.CreateAPIView):
    queryset = Restock.objects.all()
    serializer_class = RestockSerializer

    def perform_create(self, serializer):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')
        item_id = self.kwargs.get('item_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise PermissionDenied("User does not exist.")

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if shop.owner != user:
            raise PermissionDenied("You do not have permission to restock items for this shop.")

        try:
            item = Item.objects.get(id=item_id, shop=shop)
        except Item.DoesNotExist:
            raise PermissionDenied("Item does not exist or does not belong to this shop.")

        quantity = self.request.data.get('quantity')
        item.quantity += int(quantity)
        item.save()

        total_price = self.request.data.get('total_price')
        serializer.save(shop=shop, item=item, total_price=total_price)
        
        
class ShopRestocksListView(generics.ListAPIView):
    serializer_class = RestockSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view restocks for this shop.")

        return Restock.objects.filter(shop=shop)
    
    
class SaleCreateView(generics.CreateAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def perform_create(self, serializer):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')
        item_id = self.kwargs.get('item_id')

        # Debugging statements
        print(f"user_id: {user_id}")
        print(f"shop_id: {shop_id}")
        print(f"item_id: {item_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise PermissionDenied("User does not exist.")

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if shop.owner != user:
            raise PermissionDenied("You do not have permission to sell items for this shop.")

        try:
            item = Item.objects.get(id=item_id, shop=shop)
        except Item.DoesNotExist:
            raise PermissionDenied("Item does not exist or does not belong to this shop.")

        # Debugging statement
        print(f"Item: {item}")

        quantity = self.request.data.get('quantity')
        if item.quantity < int(quantity):
            raise PermissionDenied("Not enough items in stock.")

        total_price = item.selling_price * int(quantity)

        # Update the item's quantity
        item.quantity -= int(quantity)
        item.save()

        serializer.save(shop=shop, item=item, total_price=total_price)
        

class ShopSalesListView(generics.ListAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view sales for this shop.")

        return Sale.objects.filter(shop=shop)

class ShopSalesForDayView(generics.ListAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view sales for this shop.")

        # Calculate the datetime for 24 hours ago
        last_24_hours = datetime.now() - timedelta(days=1)

        return Sale.objects.filter(shop=shop, sold_at__gte=last_24_hours)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_amount = queryset.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_profit = queryset.aggregate(
            total_profit=Sum(ExpressionWrapper(F('total_price') - F('cost_price'), output_field=DecimalField()))
        )['total_profit'] or 0
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total_amount': total_amount,
            'total_profit': total_profit,
            'sales': serializer.data
        })

    
class ShopSalesForWeekView(generics.ListAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view sales for this shop.")

        # Calculate the datetime for 7 days ago
        last_7_days = datetime.now() - timedelta(days=7)

        return Sale.objects.filter(shop=shop, sold_at__gte=last_7_days)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_amount = queryset.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_profit = queryset.aggregate(
            total_profit=Sum(ExpressionWrapper(F('total_price') - F('cost_price'), output_field=DecimalField()))
        )['total_profit'] or 0
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total_amount': total_amount,
            'total_profit': total_profit,
            'sales': serializer.data 
        })
        
    
class ShopSalesForMonthView(generics.ListAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view sales for this shop.")

        # Calculate the datetime for 30 days ago
        last_30_days = datetime.now() - timedelta(days=30)

        return Sale.objects.filter(shop=shop, sold_at__gte=last_30_days)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_amount = queryset.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_profit = queryset.aggregate(
            total_profit=Sum(ExpressionWrapper(F('total_price') - F('cost_price'), output_field=DecimalField()))
        )['total_profit'] or 0
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total_amount': total_amount,
            'total_profit': total_profit,
            'sales': serializer.data
        })
        
    
class ShopSalesForYearView(generics.ListAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view sales for this shop.")

        # Calculate the datetime for 365 days ago
        last_365_days = datetime.now() - timedelta(days=365)

        return Sale.objects.filter(shop=shop, sold_at__gte=last_365_days)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_amount = queryset.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_profit = queryset.aggregate(
            total_profit=Sum(ExpressionWrapper(F('total_price') - F('cost_price'), output_field=DecimalField()))
        )['total_profit'] or 0
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total_amount': total_amount,
            'total_profit': total_profit,
            'sales': serializer.data
        })
    
class ShopItemsByCategoryView(generics.ListAPIView):
    serializer_class = ItemSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view items for this shop.")

        return Item.objects.filter(shop=shop).order_by('category')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        categories = queryset.values_list('category', flat=True).distinct()
        categorized_items = {category: ItemSerializer(queryset.filter(category=category), many=True).data for category in categories}
        return Response(categorized_items)
    
class ShopItemsByCategoryView(generics.ListAPIView):
    serializer_class = ItemSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        shop_id = self.kwargs.get('shop_id')

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view items for this shop.")

        return Item.objects.filter(shop=shop).order_by('category')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        categories = queryset.values_list('category', flat=True).distinct()
        categorized_items = {category: ItemSerializer(queryset.filter(category=category), many=True).data for category in categories}
        return Response(categorized_items)    

class InventoryAnalysisView(APIView):

    def get(self, request, shop_id, user_id):
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise PermissionDenied("Shop does not exist.")

        if str(shop.owner.id) != str(user_id):
            raise PermissionDenied("You do not have permission to view inventory for this shop.")

        # Total items in stock
        total_items = Item.objects.filter(shop=shop).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

        # Total restocked items
        total_restocked = Restock.objects.filter(shop=shop).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

        # Total sold items
        total_sold = Sale.objects.filter(shop=shop).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

        # Total profit from sales
        total_profit = Sale.objects.filter(shop=shop).aggregate(
            total_profit=Sum(F('total_price') - F('cost_price'))
        )['total_profit'] or 0

        # Items that need restocking (e.g., quantity < 10)
        items_to_restock = Item.objects.filter(shop=shop, quantity__lt=10).count()

        # Most bought item
        most_bought_item = Sale.objects.filter(shop=shop).values('item__item_name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity').first()

        # Least bought item
        least_bought_item = Sale.objects.filter(shop=shop).values('item__item_name').annotate(total_quantity=Sum('quantity')).order_by('total_quantity').first()

        data = {
            'total_items': total_items,
            'total_restocked': total_restocked,
            'total_sold': total_sold,
            'total_profit': total_profit,
            'items_to_restock': items_to_restock,
            'most_bought_item': most_bought_item,
            'least_bought_item': least_bought_item,
        }

        serializer = InventoryAnalysisSerializer(data)
        return Response(serializer.data)

@csrf_exempt
def chatbot_view(request, shop_id, user_id, item_id=None):
    if request.method == "POST":
        data = json.loads(request.body)
        message = data.get("message", "")

        # Step 1: Detect the @function
        match = re.match(r"@(\w+)\s+(\d+)\s+(\w+)(?:\s+to\s+(.+?))?(?::\s+(\w+))?$", message)
        
        if match:
            command = match.group(1)  # sales, add, inventory, new, etc.
            quantity = int(match.group(2))  # Extract quantity
            product = match.group(3)  # Extract product name
            customer = match.group(4) if match.group(4) else None  # Extract customer (if available)
            payment_method = match.group(5) if match.group(5) else "cash"  # Extract payment method (default to 'cash')

            # Step 2: Process the Command
            if command == "sales" and item_id:
                return process_sales(shop_id, item_id, user_id, product, quantity, customer, payment_method)
            elif command == "add" and item_id:
                return add_to_inventory(shop_id, item_id, user_id, product, quantity)
            elif command == "inventory" and item_id:
                return check_inventory(shop_id, item_id, user_id, product)
            elif command == "new":
                return add_new_product(shop_id, user_id, product, quantity, customer, payment_method)

        print(f"Invalid command: {message}")
        return JsonResponse({"error": f"Invalid command: {message}"}, status=400)
    print(f"Invalid request method: {request.method}")
    return JsonResponse({"error": f"Invalid request method: {request.method}"}, status=405)


def process_sales(shop_id, item_id, user_id, product, quantity, customer, payment_method):
    try:
        shop = Shop.objects.get(id=shop_id)
        if str(shop.owner.id) != str(user_id):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)

        item = Item.objects.get(id=item_id, shop=shop)
        if item.quantity < quantity:
            return JsonResponse({"error": "Not enough stock"}, status=400)
        item.quantity -= quantity
        item.save()
        total_price = item.selling_price * quantity
        Sale.objects.create(shop=shop, item=item, quantity=quantity, total_price=total_price, customer=customer, payment_method=payment_method)
        return JsonResponse({"message": f"✅ Sold {quantity} {product} to {customer}.", "total_amount": total_price})
    except Shop.DoesNotExist:
        return JsonResponse({"error": "Shop not found"}, status=404)
    except Item.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)

def add_to_inventory(shop_id, item_id, user_id, product, quantity):
    try:
        shop = Shop.objects.get(id=shop_id)
        if str(shop.owner.id) != str(user_id):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)

        item = Item.objects.get(id=item_id, shop=shop)
        item.quantity += quantity
        item.save()
        Restock.objects.create(shop=shop, item=item, quantity=quantity, total_price=item.cost_price * quantity)
        return JsonResponse({"message": f"✅ Added {quantity} {product} to inventory."})
    except Shop.DoesNotExist:
        return JsonResponse({"error": "Shop not found"}, status=404)
    except Item.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)

def check_inventory(shop_id, item_id, user_id, product):
    try:
        shop = Shop.objects.get(id=shop_id)
        if str(shop.owner.id) != str(user_id):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)

        item = Item.objects.get(id=item_id, shop=shop)
        return JsonResponse({"message": f"📊 {product} stock: {item.quantity} left"})
    except Shop.DoesNotExist:
        return JsonResponse({"error": "Shop not found"}, status=404)
    except Item.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)

def add_new_product(shop_id, user_id, item_name, category, description, cost_price, selling_price, quantity):
    try:
        shop = Shop.objects.get(id=shop_id)
        if str(shop.owner.id) != str(user_id):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)

        item = Item.objects.create(
            shop=shop,
            item_name=item_name,
            category=category,
            description=description,
            cost_price=cost_price,
            selling_price=selling_price,
            quantity=quantity
        )
        return JsonResponse({"message": f"✅ Added new product {item_name} to the shop.", "item_id": item.id})
    except Shop.DoesNotExist:
        return JsonResponse({"error": "Shop not found"}, status=404)
    

@csrf_exempt
def add_new_product_view(request, shop_id, user_id):
    if request.method == "POST":
        data = json.loads(request.body)
        message = data.get("message", "")

        # Detect the @new command
        match = re.match(r"@new\s+(\w+)\s+(\w+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+)", message)
        
        if match:
            item_name = match.group(1)  # Extract item name
            category = match.group(2)  # Extract category
            quantity = int(match.group(3))  # Extract quantity
            cost_price = float(match.group(4))  # Extract cost price
            selling_price = float(match.group(5))  # Extract selling price
            description = match.group(6)  # Extract description

            try:
                shop = Shop.objects.get(id=shop_id)
                if str(shop.owner.id) != str(user_id):
                    return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)

                item = Item.objects.create(
                    shop=shop,
                    item_name=item_name,
                    category=category,
                    description=description,
                    cost_price=cost_price,
                    selling_price=selling_price,
                    quantity=quantity
                )
                return JsonResponse({"message": f"✅ Added new product {item_name} to the shop.", "item_id": item.id})
            except Shop.DoesNotExist:
                return JsonResponse({"error": "Shop not found"}, status=404)
        
        return JsonResponse({"error": "Invalid command"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)