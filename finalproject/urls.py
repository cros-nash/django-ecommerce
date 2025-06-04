# File: urls.py
# Author: Crosby Nash (crosbyn@bu.edu), 12/26/2024
# Defines the URL patterns for the marketplace platform, mapping URLs to their corresponding views.
from django.urls import path
from . import views

urlpatterns = [
    path('home', views.ItemListView.as_view(), name='home'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('profile/change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Items
    path('items/', views.ItemListView.as_view(), name='item_list'),
    # '<int:pk>' is a path converter that captures the primary key (ID) of the item.
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/update/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    
    # Cart and Orders
    path('cart/', views.CartView.as_view(), name='view_cart'),
    path('cart/add/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/', views.UpdateCartView.as_view(), name='update_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    
    # Search
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
]
