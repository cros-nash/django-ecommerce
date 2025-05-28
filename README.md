#### Project Description
Django-ecommerce is a marketplace platform built with Django 4.2.16, allowing multiple sellers to list items for sale and buyers to browse, search, and purchase products. Key features include user authentication, shopping cart management, checkout with discount codes, and order history tracking.

#### Installation
**Prerequisites:**
- Python 3.8 or higher
- pip (or pipenv)

**Setup:**
1. Clone the repository:
   ```bash
   git clone https://github.com/cros-nash/django-ecommerce.git
   cd django-ecommerce
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   python ecommerce/manage.py migrate
   ```
5. (Optional) Create a superuser:
   ```bash
   python ecommerce/manage.py createsuperuser
   ```
6. Collect static files:
   ```bash
   python ecommerce/manage.py collectstatic
   ```
7. Run the development server:
   ```bash
   python ecommerce/manage.py runserver
   ```

#### Usage
After starting the server, open your browser at `http://127.0.0.1:8000/`:
- Register a new account or log in.
- Browse items by category or use the search feature.
- Add items to your cart, adjust quantities, or remove items.
- Apply discount codes at checkout to receive percentage or fixed-amount discounts.
- View and update your profile and order history.

#### Features
- User registration, login/logout, and password management
- User profiles with address information
- Product listing (create, update, delete) for sellers
- Item browsing by category and full-text search
- Shopping cart with quantity updates and item removal
- Checkout process with order summary and discount code support
- Order history and status tracking
- Responsive UI styled with Bootstrap 4 via Django Crispy Forms and Widget Tweaks
