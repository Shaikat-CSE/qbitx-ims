from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    
    path('clients/', views.clients, name='clients'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    path('stock/', views.stock, name='stock'),
    path('stock/create/', views.stock_create, name='stock_create'),
    
    path('reports/', views.reports, name='reports'),
    path('reports/pdf/', views.customize_pdf, name='customize_pdf'),
    path('reports/pdf/<str:report_type>/', views.generate_report_pdf, name='generate_report_pdf'),
    
    path('invoices/', views.invoices, name='invoices'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
] 