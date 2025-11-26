# Quick Start Guide

Get your premium ecommerce site up and running in minutes!

## Prerequisites
- Python 3.8+
- Node.js and npm
- Virtual environment (recommended)

## Step-by-Step Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies (for Tailwind CSS)
```bash
npm install
```

### 3. Build Tailwind CSS
```bash
npm run build-css
```

For development with auto-rebuild:
```bash
npm run watch-css
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```
SECRET_KEY=django-insecure-change-this-in-production
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create Dummy Products
```bash
python manage.py create_dummy_products
```

This will create:
- 6 categories (E-Books, Templates, Software, Courses, Graphics, Music)
- 12 premium digital products with descriptions

### 7. Create Admin User
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

### 9. Access Your Site
- **Homepage**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Products**: http://127.0.0.1:8000/products/

## Testing the Site

1. **Browse Products**: Visit the homepage to see featured products
2. **Add to Cart**: Click on any product and add it to cart
3. **View Cart**: Click the cart icon in the navbar
4. **Register/Login**: Create an account or login
5. **Checkout**: Proceed to checkout (requires Stripe test keys)
6. **View Orders**: After purchase, view orders in your account

## Features to Test

✅ Product browsing and search
✅ Category filtering
✅ Shopping cart (works for guests and logged-in users)
✅ User authentication
✅ Order management
✅ Digital product downloads (after purchase)
✅ Responsive design (test on mobile/tablet)

## Troubleshooting

### Tailwind CSS not working?
- Make sure you ran `npm run build-css`
- Check that `static/css/output.css` exists and has content
- Clear browser cache

### Static files not loading?
- Run `python manage.py collectstatic` (for production)
- Check `STATIC_URL` and `STATIC_ROOT` in settings.py

### Database errors?
- Make sure migrations are run: `python manage.py migrate`
- Check database file permissions

### Stripe payment not working?
- Add your Stripe test keys to `.env` file
- Make sure keys start with `pk_test_` and `sk_test_` for test mode

## Next Steps

1. **Customize Products**: Add your own products via admin panel
2. **Upload Images**: Add product images when creating products
3. **Add Digital Files**: Upload digital files for downloadable products
4. **Configure Stripe**: Set up real Stripe keys for production
5. **Customize Design**: Modify Tailwind config and templates

Enjoy your premium ecommerce platform! 🚀

