# File: models.py
# Author: Crosby Nash (crosbyn@bu.edu), 12/26/2024
# Defines the database models for the marketplace platform, including user profiles, items, orders, discounts, and categories.
from django.utils import timezone
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db import transaction

class UserProfile(models.Model):
    """
    Extends the default User model to include their address.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Ensures a one-to-one relationship with the User model. Deleting the user will delete this profile.

    address = models.TextField()
    # Stores the address of the user.

    def __str__(self):
        """
        Returns the username when the UserProfile instance is converted to a string.
        """
        return self.user.username


class Category(models.Model):
    """
    Represents categories to organize items into groups.
    """
    name = models.TextField()
    description = models.TextField()

    def __str__(self):
        """
        Returns the category name when the instance is converted to a string.
        """
        return self.name


class Item(models.Model):
    """
    Represents an item available for purchase.
    """
    title = models.TextField()
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='items/', null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date_listed = models.DateTimeField(auto_now_add=True)
    quantity_available = models.PositiveIntegerField(default=1)

    def __str__(self):
        """
        Returns the title of the item when the instance is converted to a string.
        """
        return self.title


class Discount(models.Model):
    """
    Represents a discount that can be applied to an item or an order.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self):
        """
        Checks if the discount is still valid.
        """
        if not self.active:
            return False
        if self.expiration_date and timezone.now() > self.expiration_date:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def __str__(self):
        """
        Returns the discount code when the instance is converted to a string.
        """
        return self.code


class Order(models.Model):
    """
    Represents a user's order, including items and the total amount.
    """
    STATUS_CHOICES = [
        ('cart', 'Cart'),
        ('shipped', 'Shipped'),
    ]
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.TextField(choices=STATUS_CHOICES, default='cart')

    def __str__(self):
        """
        Returns a string representation of the order.
        """
        return f"Order #{self.id} by {self.buyer.username}"

    def calculate_total(self):
        """
        Calculates the total amount for the order, including discounts.
        """
        total = sum(item.item.price * item.quantity for item in self.orderitem_set.all())
        if self.discount and self.discount.is_valid():
            if self.discount.discount_type == 'percentage':
                self.discount_amount = (self.discount.amount / 100) * total
            elif self.discount.discount_type == 'fixed':
                self.discount_amount = self.discount.amount
            total -= self.discount_amount
            if total < 0:
                total = 0
        else:
            self.discount_amount = Decimal('0.00')
        self.total_amount = total
        self.save()

    def remove_discount(self):
        """
        Removes the applied discount and recalculates the total amount.
        """
        self.discount = None
        self.discount_amount = Decimal('0.00')
        self.calculate_total()

    def remove_item(self, order_item_id):
        """
        Removes an item from the order and recalculates the total amount.
        """
        with transaction.atomic():
            order_item = OrderItem.objects.get(id=order_item_id, order=self)
            order_item.delete()
            self.calculate_total()

    def update_quantity(self, order_item_id, quantity):
        """
        Updates the quantity of an item in the order.
        """
        order_item = OrderItem.objects.get(id=order_item_id, order=self)
        if quantity > order_item.item.quantity_available:
            raise ValueError("Requested quantity exceeds available stock.")
        order_item.quantity = quantity
        order_item.save()

    def apply_discount_code(self, discount_code):
        """
        Applies a discount code to the order if valid.
        """
        try:
            discount = Discount.objects.get(code__iexact=discount_code, active=True)
            if not discount.is_valid():
                raise ValueError("This discount code is invalid or has expired.")
            self.discount = discount
            self.calculate_total()
        except Discount.DoesNotExist:
            raise ValueError("Invalid discount code.")

class OrderItem(models.Model):
    """
    Represents an item in an order, including its quantity.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        """
        Returns a string representation of the order item.
        """
        return f"{self.quantity} of {self.item.title} in Order #{self.order.id}"

    def total_price(self):
        """
        Calculates the total price for this order item.
        """
        return self.item.price * self.quantity