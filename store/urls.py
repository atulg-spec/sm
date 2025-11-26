from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('buy/<uuid:product_id>/', views.buy_now, name='buy_now'),
    path('checkout/<uuid:product_id>/', views.checkout, name='checkout'),
    path('checkout/<uuid:product_id>/create-order/', views.create_order, name='create_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('download/<uuid:product_id>/', views.download_product, name='download_product'),
]
