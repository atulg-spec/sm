from django.contrib import admin
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'featured', 'active', 'external_download_url', 'created_at']
    list_filter = ['category', 'featured', 'active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'upi_transaction_id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'upi_transaction_id', 'upi_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'user', 'status', 'total_amount', 'created_at', 'updated_at')
        }),
        ('UPI Payment Details', {
            'fields': ('upi_transaction_id', 'upi_id', 'payment_proof')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
