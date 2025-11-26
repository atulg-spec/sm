# Premium Ecommerce Website for Digital Products

A professional, scalable ecommerce platform built with Django and Tailwind CSS for selling digital products.

## Features

- 🛍️ **Product Management**: Full CRUD operations for digital products
- 💰 **Direct Buy**: Instant purchase without cart - buy products directly
- 💳 **UPI Payment Integration**: Accept payments via UPI ID and QR code
- 👤 **User Authentication**: Registration, login, and user profiles
- 📦 **Order Management**: Complete order tracking and history with payment verification
- 📥 **Digital Downloads**: Secure file downloads for purchased products
- 🎨 **Premium UI**: Modern, responsive design with Tailwind CSS
- 🔍 **Search & Filter**: Product search and category filtering
- ⚡ **Scalable Architecture**: Clean code structure for easy scaling

## Tech Stack

- **Backend**: Django 4.2
- **Frontend**: Tailwind CSS 3.4
- **Payment**: UPI (Unified Payments Interface) - QR code and UPI ID
- **Database**: SQLite (development), easily switchable to PostgreSQL
- **Static Files**: WhiteNoise for production

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hackerrank
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies (for Tailwind CSS)**
   ```bash
   npm install
   ```

5. **Build Tailwind CSS**
   ```bash
   npm run build-css
   ```
   Or for development with watch mode:
   ```bash
   npm run watch-css
   ```

6. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   UPI_ID=yourname@upi
   UPI_QR_CODE=/path/to/your-qr-code.png
   ```
   Note: UPI_QR_CODE is optional. You can upload your QR code image to the static folder and reference it.

7. **Run migrations**
   ```bash
   python manage.py migrate
   ```

8. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Load dummy products**
   ```bash
   python manage.py create_dummy_products
   ```

10. **Run the development server**
    ```bash
    python manage.py runserver
    ```

## Project Structure

```
ecommerce/
├── ecommerce/          # Main project settings
├── store/              # Main ecommerce app
│   ├── models.py       # Product, Order, Cart models
│   ├── views.py        # Business logic
│   ├── urls.py         # URL routing
│   └── templates/      # Store templates
├── accounts/           # User authentication app
├── static/             # Static files (CSS, JS, images)
├── media/              # User uploaded files
└── templates/          # Base templates
```

## Usage

### Admin Panel
Access the admin panel at `/admin/` to manage:
- Products and categories
- Orders
- Users
- Carts

### Key URLs
- Home: `/`
- Products: `/products/`
- Product Detail: `/products/<slug>/`
- Buy Now: `/buy/<product_id>/`
- Checkout: `/checkout/<product_id>/`
- Orders: `/orders/`
- Login: `/accounts/login/`
- Register: `/accounts/register/`

## Development

### Running Tailwind in Watch Mode
```bash
npm run watch-css
```

### Creating New Products
1. Use the admin panel at `/admin/store/product/add/`
2. Or use the management command to add more dummy products

### Adding Digital Files
When creating products in the admin panel, upload digital files in the "Digital file" field. These will be available for download after purchase.

## Production Deployment

1. Set `DEBUG = False` in `settings.py`
2. Update `ALLOWED_HOSTS`
3. Configure a production database (PostgreSQL recommended)
4. Set up proper static file serving
5. Configure email backend
6. Set up SSL/HTTPS
7. Configure Stripe webhooks for production

## License

This project is open source and available for use.

