# File: forms.py
# Author: Crosby Nash (crosbyn@bu.edu), 12/26/2024
# Defines Django forms for user registration, item management, cart operations, and user profile updates.
from django import forms
from django.contrib.auth.models import User
from .models import Item, UserProfile, OrderItem

class UserRegistrationForm(forms.ModelForm):
    """
    A form for registering new users, including password confirmation.
    """
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput
        # 'PasswordInput' widget renders the password field with masked input.
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput
    )
    address = forms.CharField(
        widget=forms.TextInput,
        label='Address'
    )
    # Custom field for address, which will be saved in the UserProfile model.

    class Meta:
        """
        Specifies the model and fields associated with this form.
        """
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def clean_password_confirm(self):
        """
        Validates that the two password fields match.
        """
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            # Raises a validation error if passwords do not match.
            raise forms.ValidationError("Passwords don't match.")
        return password_confirm

class ItemForm(forms.ModelForm):
    """
    A form for creating and updating items.
    """
    class Meta:
        """
        Specifies the model and fields for item management.
        """
        model = Item
        fields = ['title', 'description', 'price', 'image', 'category', 'quantity_available']
        # All necessary fields for creating or updating an item are included.

class UserProfileForm(forms.ModelForm):
    """
    A form for updating the user's profile information.
    """
    class Meta:
        """
        Specifies the UserProfile model and its fields.
        """
        model = UserProfile
        fields = ['address']


class UserUpdateForm(forms.ModelForm):
    """
    A form for updating the user's email address.
    """
    email = forms.EmailField()
    # Email field is explicitly declared to add validation.

    class Meta:
        """
        Specifies the model and fields for updating user information.
        """
        model = User
        fields = ['email']

class OrderItemForm(forms.ModelForm):
    """
    A form for managing individual order items.
    """
    class Meta:
        """
        Specifies the model and fields for an order item.
        """
        model = OrderItem
        fields = ['quantity']
class AddToCartForm(forms.Form):
    """
    A form for adding items to the cart with a specified quantity.
    """
    quantity = forms.IntegerField(
        min_value=1,
        label='Quantity',
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px; display: inline-block; margin-right: 10px;',
            'placeholder': '1',
        })
    )
    # Defines a simple quantity field with minimum value, validation and initial value of 1.


class UpdateQuantityForm(forms.Form):
    """
    A form for updating the quantity of an item in the cart.
    """
    quantity = forms.IntegerField(
        min_value=1,
        label='Quantity',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;',
        })
    )