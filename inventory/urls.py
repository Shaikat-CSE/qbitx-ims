from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/duplicate/<int:pk>/', views.product_duplicate, name='product_duplicate'),
    
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/create/ajax/', views.supplier_create_ajax, name='supplier_create_ajax'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    
    path('clients/', views.clients, name='clients'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/create/ajax/', views.client_create_ajax, name='client_create_ajax'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    # Category URLs
    path('categories/create/ajax/', views.category_create_ajax, name='category_create_ajax'),
    
    # Warehouse URLs
    path('warehouses/', views.warehouses, name='warehouses'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/create/ajax/', views.warehouse_create_ajax, name='warehouse_create_ajax'),
    path('warehouses/<int:pk>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),
    path('warehouses/<int:pk>/inventory/', views.warehouse_inventory, name='warehouse_inventory'),
    
    path('stock/', views.stock, name='stock'),
    path('stock/create/', views.stock_create, name='stock_create'),
    path('stock/generate-invoice/<int:transaction_id>/', views.generate_invoice_from_transaction, name='generate_invoice_from_transaction'),
    
    path('reports/', views.reports, name='reports'),
    path('reports/pdf/', views.customize_pdf, name='customize_pdf'),
    path('reports/pdf/<str:report_type>/', views.generate_report_pdf, name='generate_report_pdf'),
    
    path('invoices/', views.invoices, name='invoices'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    
    # Payment URLs
    path('payments/', views.payments, name='payments'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/transaction/<int:transaction_id>/', views.payment_for_transaction, name='payment_for_transaction'),
    
    # API endpoints
    path('api/transaction/<int:transaction_id>/', views.get_transaction_details, name='get_transaction_details'),
] 