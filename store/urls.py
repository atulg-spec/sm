from django.urls import path
from django.views.generic import TemplateView
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
    # Static pages
    path('about/', TemplateView.as_view(template_name='store/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='store/contact.html'), name='contact'),
    path('help-center/', TemplateView.as_view(template_name='store/help_center.html'), name='help_center'),
    path('faqs/', TemplateView.as_view(template_name='store/faqs.html'), name='faqs'),
    path('privacy-policy/', TemplateView.as_view(template_name='store/privacy_policy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='store/terms.html'), name='terms'),

    # Help Articles
    path('help/creating-account/', TemplateView.as_view(template_name='store/help/creating_account.html'), name='help_creating_account'),
    path('help/downloading-products/', TemplateView.as_view(template_name='store/help/downloading_products.html'), name='help_downloading_products'),
    path('help/payment-security/', TemplateView.as_view(template_name='store/help/payment_security.html'), name='help_payment_security'),
    path('help/troubleshooting-downloads/', TemplateView.as_view(template_name='store/help/troubleshooting_downloads.html'), name='help_troubleshooting_downloads'),
    path('help/managing-account/', TemplateView.as_view(template_name='store/help/managing_account.html'), name='help_managing_account'),
    path('help/refund-policy/', TemplateView.as_view(template_name='store/help/refund_policy.html'), name='help_refund_policy'),
]
