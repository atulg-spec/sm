from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
import os
from .models import Product, Category, Order, OrderItem
import qrcode
import io
import base64


def home(request):
    featured_products = Product.objects.filter(featured=True, active=True)[:6]
    latest_products = Product.objects.filter(active=True)[:8]
    free_products = Product.objects.filter(price=0, active=True)[:6]
    categories = Category.objects.all()[:6]
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'free_products': free_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    products = Product.objects.filter(active=True)
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    related_products = Product.objects.filter(
        category=product.category,
        active=True
    ).exclude(id=product.id)[:4]
    
    # Check if user has purchased this product (or if it's free)
    has_purchased = False
    can_download = False
    if request.user.is_authenticated:
        if product.is_free:
            can_download = True  # Free products can be downloaded instantly
        else:
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                order__status='completed',
                product=product
            ).exists()
            can_download = has_purchased
    
    context = {
        'product': product,
        'related_products': related_products,
        'has_purchased': has_purchased,
        'can_download': can_download,
    }
    return render(request, 'store/product_detail.html', context)


@login_required
def buy_now(request, product_id):
    """Direct buy - redirects to checkout for single product"""
    product = get_object_or_404(Product, id=product_id, active=True)
    return redirect('store:checkout', product_id=product.id)


@login_required
def checkout(request, product_id):
    """Professional checkout page for direct purchase"""
    product = get_object_or_404(Product, id=product_id, active=True)

    upi_url = f"upi://pay?pa={settings.UPI_ID}&pn={request.user.first_name}&am={product.price}&cu=INR"

    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to Base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

    
    context = {
        'product': product,
        'upi_id': settings.UPI_ID,
        'upi_qr_code': qr_image_base64,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def create_order(request, product_id):
    """Create order after UPI payment"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, active=True)
        
        upi_transaction_id = request.POST.get('upi_transaction_id', '').strip()
        upi_id = request.POST.get('upi_id', '').strip()
        payment_proof = request.FILES.get('payment_proof')
        
        if not upi_transaction_id:
            messages.error(request, "Please enter UPI Transaction ID")
            return redirect('store:checkout', product_id=product.id)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=product.price,
            upi_transaction_id=upi_transaction_id,
            upi_id=upi_id,
            payment_proof=payment_proof,
            status='pending'  # Admin will verify and mark as completed
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )
        
        messages.success(request, f"Order #{order.id} placed successfully! We will verify your payment and activate your order soon.")
        return redirect('store:order_detail', order_id=order.id)
    
    return redirect('store:product_list')


@login_required
def download_product(request, product_id):
    """Handle digital product downloads"""
    product = get_object_or_404(Product, id=product_id)
    
    # Free products can be downloaded instantly without purchase
    if product.is_free:
        # Check if external URL is provided
        if product.external_download_url:
            # Redirect to external URL - will open in new tab via template
            return redirect(product.external_download_url)
        
        if not product.digital_file:
            messages.error(request, "This product doesn't have a downloadable file.")
            return redirect('store:product_detail', slug=product.slug)
        
        file_path = product.digital_file.path
        if os.path.exists(file_path):
            return FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
            )
        else:
            raise Http404("File not found")
    
    # For paid products, check if user has purchased
    order_items = OrderItem.objects.filter(
        order__user=request.user,
        order__status='completed',
        product=product
    )
    
    if not order_items.exists():
        # Also check pending orders
        pending_order = OrderItem.objects.filter(
            order__user=request.user,
            order__status='pending',
            product=product
        ).first()
        
        if pending_order:
            messages.warning(request, "Your payment is being verified. Download will be available once payment is confirmed.")
            return redirect('store:order_detail', order_id=pending_order.order.id)
        else:
            messages.error(request, "You haven't purchased this product or your payment is still pending verification.")
            return redirect('store:product_detail', slug=product.slug)
    
    # Check if external URL is provided
    if product.external_download_url:
        # Redirect to external URL - will open in new tab via template
        return redirect(product.external_download_url)
    
    if not product.digital_file:
        messages.error(request, "This product doesn't have a downloadable file.")
        return redirect('store:product_detail', slug=product.slug)
    
    file_path = product.digital_file.path
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
    else:
        raise Http404("File not found")


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    context = {
        'orders': orders,
    }
    return render(request, 'store/order_list.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)
