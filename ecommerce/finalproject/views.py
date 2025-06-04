# File: views.py
# Author: Crosby Nash (crosbyn@bu.edu), 11/22/2024
# Description: Django views for managing user authentication, item listings, 
# shopping cart functionality, and user profiles in a marketplace platform.

from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView, View
)
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.db import transaction
from .models import Discount, Item, Category, Order, OrderItem, UserProfile
from .forms import (
    UserRegistrationForm,
    ItemForm,
    UserProfileForm,
    UserUpdateForm,
    AddToCartForm,
    UpdateQuantityForm,
)

class RegisterView(CreateView):
    """
    Handles user registration. Saves user data and creates a corresponding UserProfile.
    """
    template_name = "registration/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        """
        Saves the user instance with a password and address and creates a UserProfile.
        """
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        UserProfile.objects.create(user=user, address=form.cleaned_data["address"])
        messages.success(self.request, "Registration successful.")
        return super().form_valid(form)

class UserLoginView(LoginView):
    """
    Handles user login functionality.
    """
    template_name = "registration/login.html"
    
    # Ensures authenticated users are redirected from login page
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirects authenticated users to the home page.
        """
        return reverse_lazy("home")

class UserLogoutView(LogoutView):
    """
    Handles user logout functionality.
    """
    template_name = "registration/logout.html"

class ItemListView(ListView):
    """
    Displays a paginated list of available items for sale.
    """
    template_name = "items/item_list.html"
    context_object_name = "items"
    paginate_by = 12

    def get_queryset(self):
        """
        Retrieves items with available stock, ordered by the listing date.
        """
        return Item.objects.filter(quantity_available__gt=0).order_by("-date_listed")

class ItemDetailView(DetailView):
    """
    Displays detailed information about a specific item.
    """
    template_name = "items/item_detail.html"
    model = Item

    def get_context_data(self, **kwargs):
        """
        Adds an AddToCartForm instance to the context.
        """
        context = super().get_context_data(**kwargs)
        context["add_to_cart_form"] = AddToCartForm()
        return context

class ItemCreateView(LoginRequiredMixin, CreateView):
    """
    Allows logged-in users to create and list new items for sale.
    """
    template_name = "items/item_form.html"
    form_class = ItemForm

    def form_valid(self, form):
        """
        Assigns the logged-in user as the seller of the new item.
        """
        form.instance.seller = self.request.user
        messages.success(self.request, "Item listed successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects to the detail page of the newly listed item.
        """
        return reverse("item_detail", kwargs={"pk": self.object.pk})

class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allows logged-in users to update details of their listed items.
    """
    template_name = "items/item_form.html"
    model = Item
    form_class = ItemForm

    def get_queryset(self):
        """
        Ensures only items owned by the logged-in user can be updated.
        """
        return Item.objects.filter(seller=self.request.user)

    def form_valid(self, form):
        """
        Displays a success message after the item is updated.
        """
        messages.success(self.request, "Item updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects to the detail page of the updated item.
        """
        return reverse("item_detail", kwargs={"pk": self.object.pk})    

class ItemDeleteView(LoginRequiredMixin, DeleteView):
    """
    Allows logged-in users to delete their listed items.
    """
    model = Item
    template_name = "items/item_confirm_delete.html"
    success_url = reverse_lazy("item_list")

    def get_queryset(self):
        """
        Ensures only items owned by the logged-in user can be deleted.
        """
        return Item.objects.filter(seller=self.request.user)

    def delete(self, request, *args, **kwargs):
        """
        Displays a success message after the item is deleted.
        """
        messages.success(request, "Item deleted successfully.")
        return super().delete(request, *args, **kwargs)

class SearchView(ListView):
    """
    Handles item search functionality based on user input.
    """
    template_name = "search_results.html"
    context_object_name = "items"
    paginate_by = 12

    def get_queryset(self):
        """
        Filters items based on the search query provided by the user.
        """
        # Retrieves the value of the 'q' parameter from the URL query string.
        query = self.request.GET.get("q", "")
        # Filters items that match the search query in their title or description and have available stock.
        return Item.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query), quantity_available__gt=0
        ).distinct()  # ensures duplicate results are not included.

    def get_context_data(self, **kwargs):
        """
        Adds the search query to the context to display it on the search results page.
        """
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context

class AddToCartView(LoginRequiredMixin, View):
    """
    Handles adding items to the shopping cart for logged-in users.
    """
    def post(self, request, *args, **kwargs):
        """
        Adds the specified quantity of an item to the user's cart.
        """
        # Retrieves the item based on the primary key passed in the URL.
        item = get_object_or_404(Item, id=kwargs["pk"])
        form = AddToCartForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data["quantity"]

            # Check if the requested quantity is available in stock.
            if quantity > item.quantity_available:
                messages.error(
                    request,
                    f"Requested quantity exceeds available stock ({item.quantity_available})."
                )
                return redirect("item_detail", item.pk)

            # Ensures all database updates occur as a single unit.
            # since modifications to the database are being made, this ensures that the changes will
            # only happen if all operations run without any errors
            with transaction.atomic():
                # Finds an existing cart or creates a new one for the user.
                order, _ = Order.objects.get_or_create(buyer=request.user, status="cart")
                # Adds the item to the cart or updates its quantity if it already exists.
                order_item, _ = OrderItem.objects.get_or_create(
                    order=order, item=item, defaults={"quantity": 0}
                )
                # Update the quantity of item.
                order_item.quantity += quantity
                order_item.save()

                # Update the total cost of the cart.
                order.total_amount += item.price * quantity
                order.save()

            messages.success(request, f"Added {quantity} x {item.title} to your cart.")
            return redirect("view_cart")
        else:
            messages.error(request, "Invalid quantity. Please enter a valid number.")
            return redirect("item_detail", item.pk)

class CartView(LoginRequiredMixin, TemplateView):
    """
    Displays the current user's shopping cart.
    """
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        """
        Adds order and order item details to the context for rendering the cart.
        """
        context = super().get_context_data(**kwargs)
        # Retrieves the user's current cart or creates a new one if it doesn't exist.
        order, _ = Order.objects.get_or_create(buyer=self.request.user, status="cart")
        order_items = OrderItem.objects.filter(order=order)
        total = order.total_amount 

        # Prepares forms for updating item quantities in the cart.
        update_forms = {
            item.id: UpdateQuantityForm(initial={"quantity": item.quantity}) for item in order_items
        }

        # Adds all required data to the context dictionary.
        context.update({
            "order": order,
            "order_items": order_items,
            "total": total,
            "update_quantity_forms": update_forms,
        })
        return context

class UpdateCartView(LoginRequiredMixin, View):
    """
    Handles updates to the shopping cart, including removing items or applying discounts.
    """
    def post(self, request, *args, **kwargs):
        """
        Updates the cart based on user actions (e.g., changing quantities or applying discount codes).
        """
        # Fetch the current cart or create one if it doesn't exist.
        order, _ = Order.objects.get_or_create(buyer=request.user, status="cart")

        # Removes any applied discount from the cart.
        if request.POST.get("remove_discount"):
            
            order.remove_discount()
            messages.success(request, "Discount removed successfully.")
            return redirect("view_cart")

        # Remove an item from the cart.
        if remove_item_id := request.POST.get("remove_item"):
            try:
                order.remove_item(remove_item_id)
                messages.success(request, "Item removed from your cart.")
            except Exception:
                messages.error(request, "An error occurred while removing the item.")
            return redirect("view_cart")

        updated = False  # Tracks if any item quantities were updated.

        # Process each form field in the POST data.
        for key, value in request.POST.items():
            if key.startswith("quantity_"):
                order_item_id = key.split("_")[1]
                try:
                    quantity = int(value)
                    order.update_quantity(order_item_id, quantity)  # Updates the item quantity.
                    updated = True
                except ValueError as e:
                    messages.error(request, str(e))

        # Apply a discount code if provided.
        if discount_code := request.POST.get("discount_code"):
            try:
                order.apply_discount_code(discount_code)
                messages.success(request, f'Discount "{discount_code}" applied successfully.')
            except ValueError as e:
                messages.error(request, str(e))

        if updated:
            order.calculate_total()  # Recalculates the total cost after updates.
            messages.success(request, "Cart updated successfully.")
        return redirect("view_cart")

class CheckoutView(LoginRequiredMixin, TemplateView):
    """
    Handles the checkout process for users.
    """
    template_name = "checkout.html"

    def get_order(self):
        """
        Retrieves the current user's cart for checkout.
        """
        return get_object_or_404(Order, buyer=self.request.user, status="cart")

    def get_context_data(self, **kwargs):
        """
        Adds the cart to the context for rendering the checkout page.
        """
        context = super().get_context_data(**kwargs)
        context['order'] = self.get_order()
        return context

    def post(self, request, *args, **kwargs):
        """
        Finalizes the checkout process and updates item stock quantities.
        """
        order = self.get_order()
        with transaction.atomic():
            # Marks the order as 'shipped'.
            order.status = "shipped"
            order.save()

            for order_item in OrderItem.objects.filter(order=order):
                item = order_item.item
                # Ensures sufficient stock is available before reducing quantities.
                if item.quantity_available >= order_item.quantity:
                    item.quantity_available -= order_item.quantity
                    item.save()
                else:
                    messages.error(request, f"Not enough stock for {item.title}.")
                    return redirect("view_cart")

        messages.success(request, "Checkout successful! Your order has been placed.")
        return redirect("profile")

class OrderHistoryView(LoginRequiredMixin, ListView):
    """
    Displays a history of the user's past orders.
    """
    template_name = "order_history.html"
    context_object_name = "orders"

    def get_queryset(self):
        """
        Retrieves all completed orders for the logged-in user, ordered by the date.
        """
        # Excludes the "cart" status because those are incomplete orders.
        return Order.objects.filter(buyer=self.request.user).exclude(status="cart").order_by("-order_date")

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Displays the user's profile, including personal information, items for sale, and purchase history.
    """
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        """
        Adds user details, items for sale, and order history to the context.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Retrieves the currently logged-in user.
        user_profile = get_object_or_404(UserProfile, user=user)
        items_for_sale = Item.objects.filter(seller=user)
        # Retrieves past orders for the user (excluding the cart).
        purchase_orders = Order.objects.filter(buyer=user).exclude(status="cart").order_by("-order_date")

        # Adds order totals for each order, including discounts.
        orders_with_totals = []
        for order in purchase_orders:
            order_items = OrderItem.objects.filter(order=order)
            total_without_discount = sum(order_item.item.price * order_item.quantity for order_item in order_items)
            orders_with_totals.append({
                "order": order,
                "total_without_discount": total_without_discount,
                "discount": order.discount,
                "discount_amount": order.discount_amount,
                "final_total": order.total_amount
            })

        # Updates the context with all required data.
        context.update({
            "user": user,
            "user_profile": user_profile,
            "items_for_sale": items_for_sale,
            "purchase_orders": orders_with_totals,
        })
        return context

class UpdateProfileView(LoginRequiredMixin, View):
    """
    Handles updating the user's profile information.
    """
    template_name = "update_profile.html"

    def get(self, request, *args, **kwargs):
        """
        Displays the profile update form with the user's current information pre-filled.
        """
        user = request.user
        user_profile = get_object_or_404(UserProfile, user=user)
        user_form = UserUpdateForm(instance=user)  # Pre-fills the user update form.
        profile_form = UserProfileForm(instance=user_profile)  # Pre-fills the profile update form.
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})

    def post(self, request, *args, **kwargs):
        """
        Handles submission of the profile update form.
        """
        user = request.user
        user_profile = get_object_or_404(UserProfile, user=user)
        # Binds the form to the submitted POST data.
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            # Saves the updated information to the database.
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
        # Renders the form again with validation errors if the input is invalid.
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})


class ChangePasswordView(PasswordChangeView):
    """
    Allows users to change their account password.
    """
    template_name = "change_password.html"
    success_url = reverse_lazy("profile")  # Redirects to the profile page upon success.

    def form_valid(self, form):
        """
        Displays a success message when the password is successfully updated.
        """
        messages.success(self.request, "Your password was successfully updated!")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Displays an error message when the password update fails.
        """
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

class CategoryListView(ListView):
    """
    Displays a list of categories with the count of in-stock items in each category.
    """
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        """
        Retrieves categories that have at least one item in stock, sorted alphabetically.
        """
        # 'annotate' adds in-stock item count field to the query
        return Category.objects.annotate(
            in_stock_item_count=Count("item", filter=Q(item__quantity_available__gt=0))
        ).filter(in_stock_item_count__gt=0).order_by("name")

class CategoryDetailView(DetailView):
    """
    Displays detailed information about a specific category and its items.
    """
    template_name = "categories/category_detail.html"
    model = Category
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        """
        Adds a list of items in the category to the context, sorted based on user selection.
        """
        context = super().get_context_data(**kwargs)
        # Retrieves the sorting option chosen by the user (if any).
        sort_option = self.request.GET.get("sort", "")
        # Filters items in the current category with available stock.
        items = Item.objects.filter(category=self.object, quantity_available__gt=0)

        # Sorts the items based on the selected option.
        if sort_option == "price_asc":
            items = items.order_by("price")
        elif sort_option == "price_desc":
            items = items.order_by("-price")
        elif sort_option == "date_new":
            items = items.order_by("-date_listed")
        elif sort_option == "date_old":
            items = items.order_by("date_listed")
        else:
            items = items.order_by("-date_listed")  # Default sorting by newest first.

        context["items"] = items
        return context