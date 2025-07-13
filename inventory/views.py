from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Count
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_POST
import uuid

from .models import Product, Category, Supplier, Client, StockTransaction, Invoice, Warehouse, Payment
from .forms import (
    ProductForm, CategoryForm, SupplierForm, ClientForm, 
    StockTransactionForm, InvoiceForm, InvoiceItemFormSet, WarehouseForm, PaymentForm
)
from .utils import render_to_pdf
from .decorators import (
    view_dashboard_required, view_products_required, 
    add_products_required, change_products_required, delete_products_required,
    view_suppliers_required, add_suppliers_required, change_suppliers_required, delete_suppliers_required,
    view_clients_required, add_clients_required, change_clients_required, delete_clients_required,
    view_stock_required, add_stock_required, view_reports_required,
    view_invoices_required, add_invoices_required
)

# Warehouse views
@login_required
def warehouses(request):
    """View all warehouses"""
    warehouses_list = Warehouse.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        warehouses_list = warehouses_list.filter(
            Q(name__icontains=search_query) | Q(location__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(warehouses_list, 10)  # Show 10 warehouses per page
    page = request.GET.get('page')
    warehouses = paginator.get_page(page)
    
    context = {
        'warehouses': warehouses,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/warehouses.html', context)

@login_required
def warehouse_create(request):
    """Create a new warehouse"""
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Warehouse created successfully')
            return redirect('warehouses')
    else:
        form = WarehouseForm()
    
    return render(request, 'inventory/warehouse_form.html', {
        'form': form,
        'title': 'Create Warehouse'
    })

@login_required
def warehouse_edit(request, pk):
    """Edit an existing warehouse"""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, 'Warehouse updated successfully')
            return redirect('warehouses')
    else:
        form = WarehouseForm(instance=warehouse)
    
    return render(request, 'inventory/warehouse_form.html', {
        'form': form,
        'warehouse': warehouse,
        'title': 'Edit Warehouse'
    })

@login_required
def warehouse_delete(request, pk):
    """Delete a warehouse"""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    
    if request.method == 'POST':
        # Check if warehouse has products
        if warehouse.products.exists():
            messages.error(request, 'Cannot delete warehouse with associated products')
            return redirect('warehouses')
        
        warehouse.delete()
        messages.success(request, 'Warehouse deleted successfully')
        return redirect('warehouses')
    
    return render(request, 'inventory/warehouse_confirm_delete.html', {
        'warehouse': warehouse
    })

@login_required
def warehouse_inventory(request, pk):
    """View inventory in a specific warehouse"""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    products = Product.objects.filter(warehouse=warehouse).order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(sku__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'warehouse': warehouse,
        'products': products_page,
        'search_query': search_query,
        'total_products': products.count(),
        'low_stock_count': products.filter(quantity__lte=F('reorder_level')).count(),
    }
    
    return render(request, 'inventory/warehouse_inventory.html', context)

@view_dashboard_required
def dashboard(request):
    today = timezone.now().date()
    
    # Get basic stats
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    
    # Calculate inventory value
    inventory_value = Product.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('buying_price'), output_field=DecimalField()))
    )['total'] or 0
    
    # Get wastage - use wastage_amount field directly
    total_wastage = StockTransaction.objects.filter(
        Q(transaction_type='wastage') | Q(wastage_amount__gt=0)
    ).aggregate(
        total=Sum('wastage_amount')
    )['total'] or 0
    
    # Get due payments (money owed to us) - sales with due payment status
    due_payments = StockTransaction.objects.filter(
        transaction_type='out', 
        payment_status__in=['due', 'partial']
    ).aggregate(
        total=Sum('amount_due')
    )['total'] or 0
    
    # Get due payables (money we owe) - purchases with due payment status
    due_payables = StockTransaction.objects.filter(
        transaction_type='in', 
        payment_status__in=['due', 'partial']
    ).aggregate(
        total=Sum('amount_due')
    )['total'] or 0
    
    # Get recent due payments (top 5)
    recent_due_payments = StockTransaction.objects.filter(
        transaction_type='out', 
        payment_status__in=['due', 'partial']
    ).order_by('-transaction_date')[:5]
    
    # Get recent due payables (top 5)
    recent_due_payables = StockTransaction.objects.filter(
        transaction_type='in', 
        payment_status__in=['due', 'partial']
    ).order_by('-transaction_date')[:5]
    
    # Top products by value
    top_products_by_value = Product.objects.annotate(
        total_value=ExpressionWrapper(F('quantity') * F('buying_price'), output_field=DecimalField())
    ).order_by('-total_value')[:5]
    
    top_products_labels = [p.name for p in top_products_by_value]
    top_products_values = [float(p.total_value) for p in top_products_by_value]
    
    # Products by category
    categories = Category.objects.all()
    category_labels = [c.name for c in categories]
    category_values = []
    
    for category in categories:
        count = Product.objects.filter(category=category).count()
        category_values.append(count)
    
    # Sales trend for last 30 days
    last_30_days = today - timedelta(days=30)
    sales_data = StockTransaction.objects.filter(
        transaction_type='out',
        transaction_date__gte=last_30_days
    ).values('transaction_date__date').annotate(
        total=Sum(ExpressionWrapper(F('quantity') * F('selling_price'), output_field=DecimalField()))
    ).order_by('transaction_date__date')
    
    sales_dates = []
    sales_values = []
    
    for i in range(30):
        date = last_30_days + timedelta(days=i)
        sales_dates.append(date.strftime('%Y-%m-%d'))
        
        # Find if there's a sale on this date
        sale_value = 0
        for sale in sales_data:
            if sale['transaction_date__date'] == date:
                sale_value = float(sale['total'])
                break
        
        sales_values.append(sale_value)
    
    # Top 50 products
    top_products = Product.objects.all().order_by('-quantity')[:50]
    
    # Calculate recent sales (last 24 hours)
    yesterday = today - timedelta(days=1)
    recent_sales = StockTransaction.objects.filter(
        transaction_type='out',
        transaction_date__gte=yesterday
    ).aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    # Get pending invoices count
    pending_invoices_count = Invoice.objects.filter(status='pending').count()
    
    # Products expiring in next 30 days
    thirty_days_later = today + timedelta(days=30)
    expiring_soon_count = Product.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=thirty_days_later
    ).count()
    
    context = {
        'today': today,
        'total_products': total_products,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'total_wastage': total_wastage,
        'due_payments': due_payments,
        'due_payables': due_payables,
        'recent_due_payments': recent_due_payments,
        'recent_due_payables': recent_due_payables,
        'top_products': top_products,
        'top_products_labels': json.dumps(top_products_labels),
        'top_products_values': json.dumps(top_products_values),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'sales_dates': json.dumps(sales_dates),
        'sales_values': json.dumps(sales_values),
        'recent_sales': recent_sales,
        'pending_invoices_count': pending_invoices_count,
        'expiring_soon_count': expiring_soon_count,
    }
    
    return render(request, 'inventory/dashboard.html', context)

@view_products_required
def products(request):
    categories = Category.objects.all()
    warehouses = Warehouse.objects.all()
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    products_list = Product.objects.all().order_by('id')  # Add default ordering
    
    if category_id:
        products_list = products_list.filter(category_id=category_id)
    
    if search_query:
        # If search_query is numeric, treat as ID
        if search_query.isdigit():
            products_list = products_list.filter(id=int(search_query))
        else:
            products_list = products_list.filter(
                Q(name__icontains=search_query) | Q(sku__icontains=search_query)
            )
    
    # Return JSON if requested
    if request.GET.get('format') == 'json':
        products_data = []
        for product in products_list:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category_id': product.category_id,
                'category_name': product.category.name if product.category else None,
                'description': product.description,
                'buying_price': float(product.buying_price),
                'selling_price': float(product.selling_price),
                'unit_of_measure': product.unit_of_measure,
                'quantity': product.quantity,
                'supplier_id': product.supplier_id,
                'supplier_name': product.supplier.name if product.supplier else None,
                'warehouse_id': product.warehouse_id,
                'warehouse_name': product.warehouse.name if product.warehouse else None,
            })
        return JsonResponse(products_data, safe=False)
    
    # Pagination
    paginator = Paginator(products_list, 10)  # Show 10 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': categories,
        'warehouses': warehouses,
        'category_id': category_id,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/products.html', context)

@add_products_required
def product_create(request):
    # Get filter parameters to preserve them after redirect
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    page = request.GET.get('page')
    
    # Build redirect URL parameters
    redirect_params = {}
    if category_id:
        redirect_params['category'] = category_id
    if search_query:
        redirect_params['search'] = search_query
    if page:
        redirect_params['page'] = page
        
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully.')
            
            # Redirect with preserved filter parameters
            if redirect_params:
                redirect_url = reverse('products') + '?' + urlencode(redirect_params)
                return redirect(redirect_url)
            return redirect('products')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'inventory/product_form.html', context)

@change_products_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Get filter parameters to preserve them after redirect
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    page = request.GET.get('page')
    
    # Build redirect URL parameters
    redirect_params = {}
    if category_id:
        redirect_params['category'] = category_id
    if search_query:
        redirect_params['search'] = search_query
    if page:
        redirect_params['page'] = page
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully.')
            
            # Redirect with preserved filter parameters
            if redirect_params:
                redirect_url = reverse('products') + '?' + urlencode(redirect_params)
                return redirect(redirect_url)
            return redirect('products')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    
    return render(request, 'inventory/product_form.html', context)

@delete_products_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Get filter parameters to preserve them after redirect
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    page = request.GET.get('page')
    
    # Build redirect URL parameters
    redirect_params = {}
    if category_id:
        redirect_params['category'] = category_id
    if search_query:
        redirect_params['search'] = search_query
    if page:
        redirect_params['page'] = page
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully.')
        
        # Redirect with preserved filter parameters
        if redirect_params:
            redirect_url = reverse('products') + '?' + urlencode(redirect_params)
            return redirect(redirect_url)
        return redirect('products')
    
    # If not POST, redirect back to products with preserved filters
    if redirect_params:
        redirect_url = reverse('products') + '?' + urlencode(redirect_params)
        return redirect(redirect_url)
    return redirect('products')

@view_suppliers_required
def suppliers(request):
    search_query = request.GET.get('search', '')
    
    suppliers_list = Supplier.objects.all().order_by('name')
    
    if search_query:
        suppliers_list = suppliers_list.filter(
            Q(name__icontains=search_query) | 
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(suppliers_list, 10)  # Show 10 suppliers per page
    page = request.GET.get('page')
    suppliers = paginator.get_page(page)
    
    context = {
        'suppliers': suppliers,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/suppliers.html', context)

@add_suppliers_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" created successfully.')
            return redirect('suppliers')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'inventory/supplier_form.html', context)

@change_suppliers_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get related transactions for this supplier
    related_transactions = StockTransaction.objects.filter(supplier=supplier).order_by('-transaction_date')[:10]
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
            return redirect('suppliers')
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
        'related_transactions': related_transactions,
    }
    
    return render(request, 'inventory/supplier_form.html', context)

@delete_suppliers_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier "{supplier_name}" deleted successfully.')
        return redirect('suppliers')
    
    return redirect('suppliers')

@view_clients_required
def clients(request):
    search_query = request.GET.get('search', '')
    
    clients_list = Client.objects.all().order_by('name')
    
    if search_query:
        clients_list = clients_list.filter(
            Q(name__icontains=search_query) | 
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(clients_list, 10)  # Show 10 clients per page
    page = request.GET.get('page')
    clients = paginator.get_page(page)
    
    context = {
        'clients': clients,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/clients.html', context)

@add_clients_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" created successfully.')
            return redirect('clients')
    else:
        form = ClientForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'inventory/client_form.html', context)

@change_clients_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    # Get related transactions for this client
    related_transactions = StockTransaction.objects.filter(client=client).order_by('-transaction_date')[:10]
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" updated successfully.')
            return redirect('clients')
    else:
        form = ClientForm(instance=client)
    
    context = {
        'form': form,
        'client': client,
        'related_transactions': related_transactions,
    }
    
    return render(request, 'inventory/client_form.html', context)

@delete_clients_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully.')
        return redirect('clients')
    
    return redirect('clients')

@view_stock_required
def stock(request):
    transaction_type = request.GET.get('type', '')
    product_id = request.GET.get('product_id', '')
    supplier_id = request.GET.get('supplier_id', '')
    client_id = request.GET.get('client_id', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('search', '')
    
    transactions_list = StockTransaction.objects.all().order_by('-transaction_date')
    
    # Apply filters
    if transaction_type:
        transactions_list = transactions_list.filter(transaction_type=transaction_type)
    
    if product_id:
        transactions_list = transactions_list.filter(product_id=product_id)
    
    if supplier_id:
        transactions_list = transactions_list.filter(supplier_id=supplier_id)
    
    if client_id:
        transactions_list = transactions_list.filter(client_id=client_id)
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            transactions_list = transactions_list.filter(transaction_date__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions_list = transactions_list.filter(transaction_date__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # Apply search query
    if search_query:
        transactions_list = transactions_list.filter(
            Q(transaction_id__icontains=search_query) |
            Q(product__name__icontains=search_query) | 
            Q(reference_number__icontains=search_query)
        )
    
    # Return JSON if requested
    if request.GET.get('format') == 'json':
        transactions_data = []
        for transaction in transactions_list:
            transactions_data.append({
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'product_id': transaction.product_id,
                'product_name': transaction.product.name if transaction.product else None,
                'transaction_type': transaction.transaction_type,
                'transaction_date': transaction.transaction_date.isoformat(),
                'quantity': transaction.quantity,
                'buying_price': float(transaction.buying_price),
                'selling_price': float(transaction.selling_price),
                'unit_price': float(transaction.unit_price),
                'total_price': float(transaction.total_price),
                'payment_status': transaction.payment_status,
                'amount_paid': float(transaction.amount_paid) if transaction.amount_paid else 0,
                'amount_due': float(transaction.amount_due) if transaction.amount_due else 0,
                'reference_number': transaction.reference_number,
                'notes': transaction.notes,
            })
        return JsonResponse(transactions_data, safe=False)
    
    # Check which transactions already have invoices
    transaction_invoices = {}
    invoice_data = []
    for transaction in transactions_list:
        if transaction.transaction_type == 'out' and transaction.client:
            reference_number = f"TRANS-{transaction.id}"
            invoice = Invoice.objects.filter(notes__contains=reference_number).first()
            if invoice:
                transaction_invoices[transaction.id] = invoice.id
                invoice_data.append({
                    'transaction_id': transaction.id,
                    'invoice_id': invoice.id
                })
    
    # Pagination
    paginator = Paginator(transactions_list, 10)  # Show 10 transactions per page
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    
    # Get all products for the filter dropdown
    products = Product.objects.all().order_by('name')
    
    context = {
        'transactions': transactions,
        'products': products,
        'transaction_type': transaction_type,
        'product_id': int(product_id) if product_id else None,
        'supplier_id': int(supplier_id) if supplier_id else None,
        'client_id': int(client_id) if client_id else None,
        'start_date': start_date,
        'end_date': end_date,
        'transaction_invoices': transaction_invoices,
        'invoice_data': invoice_data,
    }
    
    return render(request, 'inventory/stock.html', context)

@add_stock_required
def stock_create(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            
            # Handle tax calculations if applicable
            if transaction.transaction_type == 'out' and request.POST.get('apply_taxes') == 'True':
                transaction.apply_taxes = True
                transaction.vat_rate = float(request.POST.get('vat_rate', 0))
                transaction.ait_rate = float(request.POST.get('ait_rate', 0))
                transaction.final_price = float(request.POST.get('final_price', 0))
                
                # Set unit_price to final_price after tax deductions
                transaction.unit_price = transaction.final_price
                # Update total_price to reflect tax deductions
                transaction.total_price = transaction.quantity * transaction.final_price
            else:
                # Set unit_price based on transaction type
                if transaction.transaction_type == 'out':
                    transaction.unit_price = transaction.selling_price
                else:
                    transaction.unit_price = transaction.buying_price
            
            transaction.save()
            
            # Check if an invoice was automatically generated
            if transaction.transaction_type == 'out' and transaction.client:
                invoice = transaction.generate_invoice()
                if invoice:
                    messages.success(
                        request, 
                        f'Stock transaction created successfully. An invoice (#{invoice.invoice_number}) has been automatically generated.'
                    )
                else:
                    messages.success(request, f'Stock transaction created successfully.')
            else:
                messages.success(request, f'Stock transaction created successfully.')
                
            return redirect('stock')
    else:
        form = StockTransactionForm(initial={'transaction_date': timezone.now()})
    
    context = {
        'form': form,
        'title': 'Add Stock Transaction'
    }
    
    return render(request, 'inventory/stock_form.html', context)

@view_reports_required
def reports(request):
    # Get all models for filtering
    all_products = Product.objects.all().order_by('name')
    all_categories = Category.objects.all().order_by('name')
    all_suppliers = Supplier.objects.all().order_by('name')
    all_clients = Client.objects.all().order_by('name')
    
    today = timezone.now().date()
    
    # Get customization from session or use defaults
    customization = request.session.get('pdf_customization', {
        'company_name': 'QBITX IMS',
        'company_tagline': 'Transform Suppliers',
        'company_details': '123 Business Street, Business City, Country',
        'terms_conditions': '',
    })
    
    # Get report type
    report_type = request.GET.get('type', 'inventory')
    
    # Get filter parameters
    product_id = request.GET.get('product_id')
    category_id = request.GET.get('category_id')
    supplier_id = request.GET.get('supplier_id')
    client_id = request.GET.get('client_id')
    group_by = request.GET.get('group_by')
    sort_by = request.GET.get('sort_by', 'date_desc')
    payment_status = request.GET.get('payment_status')
    
    # Track applied filters for display
    applied_filters = []
    
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        applied_filters.append(f"Product: {product.name}")
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        applied_filters.append(f"Category: {category.name}")
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id)
        applied_filters.append(f"Supplier: {supplier.name}")
    if client_id:
        client = get_object_or_404(Client, id=client_id)
        applied_filters.append(f"Client: {client.name}")
    if payment_status and report_type == 'payment':
        payment_status_display = dict(StockTransaction.PAYMENT_STATUS_CHOICES).get(payment_status, 'Unknown')
        applied_filters.append(f"Payment Status: {payment_status_display}")
        
    # Group by display name
    group_by_display = None
    if group_by:
        group_by_display = {
            'product': 'Product',
            'category': 'Category',
            'supplier': 'Supplier',
            'client': 'Client',
            'date': 'Date',
        }.get(group_by)
        applied_filters.append(f"Grouped by: {group_by_display}")
    
    # Set default date range if not provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = today.strftime('%Y-%m-%d')
    
    # Convert string dates to datetime objects
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = today - timedelta(days=30)
        end_date_obj = today
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # Initialize context
    context = {
        'report_type': report_type,
        'all_products': all_products,
        'all_categories': all_categories,
        'all_suppliers': all_suppliers,
        'all_clients': all_clients,
        'product_id': int(product_id) if product_id else None,
        'category_id': int(category_id) if category_id else None,
        'supplier_id': int(supplier_id) if supplier_id else None,
        'client_id': int(client_id) if client_id else None,
        'group_by': group_by,
        'group_by_display': group_by_display,
        'sort_by': sort_by,
        'payment_status': payment_status,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
        'applied_filters': ', '.join(applied_filters) if applied_filters else None,
    }
    
    # Generate report based on type
    if report_type == 'inventory':
        # Inventory value report
        products = Product.objects.all()
        
        # Apply filters
        if product_id:
            products = products.filter(id=product_id)
        if category_id:
            products = products.filter(category_id=category_id)
        if supplier_id:
            products = products.filter(supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'quantity_desc':
            products = products.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            products = products.order_by('quantity')
        elif sort_by == 'price_desc':
            products = products.order_by('-buying_price')
        elif sort_by == 'price_asc':
            products = products.order_by('buying_price')
        else:
            products = products.order_by('name')  # Default sort
        
        # Calculate total value for each product
        for product in products:
            product.total_value = product.quantity * product.buying_price
        
        total_value = sum(p.total_value for p in products)
        total_quantity = sum(p.quantity for p in products)
        
        context.update({
            'report_title': 'Inventory Value Report',
            'products': products,
            'total_value': total_value,
            'total_quantity': total_quantity,
        })
    
    elif report_type == 'sales':
        # Sales report
        sales = StockTransaction.objects.filter(
            transaction_type='out',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).select_related('product', 'product__category', 'product__supplier', 'client')
        
        # Apply filters
        if product_id:
            sales = sales.filter(product_id=product_id)
        if category_id:
            sales = sales.filter(product__category_id=category_id)
        if supplier_id:
            sales = sales.filter(product__supplier_id=supplier_id)
        if client_id:
            sales = sales.filter(client_id=client_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            sales = sales.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            sales = sales.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            sales = sales.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            sales = sales.order_by('quantity')
        elif sort_by == 'price_desc':
            sales = sales.order_by('-total_price')
        elif sort_by == 'price_asc':
            sales = sales.order_by('total_price')
        
        # Calculate total sales
        total_sales = sales.aggregate(total=Sum('total_price'))['total'] or 0
        total_quantity_sold = sales.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for sale in sales:
                    product_id = sale.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': sale.product.name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    products_dict[product_id]['transactions'].append(sale)
                    products_dict[product_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for sale in sales:
                    category_id = sale.product.category_id if sale.product.category else 0
                    category_name = sale.product.category.name if sale.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    categories_dict[category_id]['transactions'].append(sale)
                    categories_dict[category_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for sale in sales:
                    supplier_id = sale.product.supplier_id if sale.product.supplier else 0
                    supplier_name = sale.product.supplier.name if sale.product.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(sale)
                    suppliers_dict[supplier_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'client':
                # Group by client
                clients_dict = {}
                for sale in sales:
                    client_id = sale.client_id if sale.client else 0
                    client_name = sale.client.name if sale.client else 'No Client'
                    
                    if client_id not in clients_dict:
                        clients_dict[client_id] = {
                            'name': client_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    clients_dict[client_id]['transactions'].append(sale)
                    clients_dict[client_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for client_id, data in clients_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for sale in sales:
                    date_str = sale.transaction_date.strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': sale.transaction_date.strftime('%B %d, %Y'),
                            'transactions': [],
                            'subtotal': 0
                        }
                    dates_dict[date_str]['transactions'].append(sale)
                    dates_dict[date_str]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
        
        context.update({
            'report_title': 'Sales Report',
            'sales': sales,
            'total_sales': total_sales,
            'total_quantity_sold': total_quantity_sold,
            'grouped_data': grouped_data,
        })
    
    elif report_type == 'purchase':
        # Purchase report (stock in transactions)
        purchases = StockTransaction.objects.filter(
            transaction_type='in',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).select_related('product', 'product__category', 'product__supplier')
        
        # Apply filters
        if product_id:
            purchases = purchases.filter(product_id=product_id)
        if category_id:
            purchases = purchases.filter(product__category_id=category_id)
        if supplier_id:
            purchases = purchases.filter(product__supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            purchases = purchases.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            purchases = purchases.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            purchases = purchases.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            purchases = purchases.order_by('quantity')
        elif sort_by == 'price_desc':
            purchases = purchases.order_by('-total_price')
        elif sort_by == 'price_asc':
            purchases = purchases.order_by('total_price')
        
        # Calculate total purchases
        total_purchases = purchases.aggregate(total=Sum('total_price'))['total'] or 0
        total_quantity_purchased = purchases.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for purchase in purchases:
                    product_id = purchase.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': purchase.product.name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    products_dict[product_id]['transactions'].append(purchase)
                    products_dict[product_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for purchase in purchases:
                    category_id = purchase.product.category_id if purchase.product.category else 0
                    category_name = purchase.product.category.name if purchase.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    categories_dict[category_id]['transactions'].append(purchase)
                    categories_dict[category_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for purchase in purchases:
                    supplier_id = purchase.product.supplier_id if purchase.product.supplier else 0
                    supplier_name = purchase.product.supplier.name if purchase.product.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(purchase)
                    suppliers_dict[supplier_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for purchase in purchases:
                    date_str = purchase.transaction_date.strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': purchase.transaction_date.strftime('%B %d, %Y'),
                            'transactions': [],
                            'subtotal': 0
                        }
                    dates_dict[date_str]['transactions'].append(purchase)
                    dates_dict[date_str]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
        
        # Ensure start_date and end_date are datetime objects for formatting
        if isinstance(start_date, str):
            start_date_formatted = start_date_obj.strftime('%b %d, %Y')
        else:
            start_date_formatted = start_date.strftime('%b %d, %Y')
            
        if isinstance(end_date, str):
            end_date_formatted = end_date_obj.strftime('%b %d, %Y')
        else:
            end_date_formatted = end_date.strftime('%b %d, %Y')
        
        context = {
            'title': 'Purchase Report',
            'report_title': 'Purchase Report',
            'report_subtitle': f"From {start_date_formatted} to {end_date_formatted}",
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'purchases': purchases,
            'grouped_data': grouped_data,
            'total_purchases': total_purchases,
            'total_quantity_purchased': total_quantity_purchased,
            'start_date': start_date,
            'end_date': end_date,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'wastage':
        # Wastage report
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Add date range to applied filters
        applied_filters.append(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get wastage transactions 
        wastage = StockTransaction.objects.filter(
            transaction_type='wastage',  # Focus only on actual wastage transactions
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Apply additional filters
        if product_id:
            wastage = wastage.filter(product_id=product_id)
        if category_id:
            wastage = wastage.filter(product__category_id=category_id)
        if supplier_id:
            wastage = wastage.filter(product__supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            wastage = wastage.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            wastage = wastage.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            wastage = wastage.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            wastage = wastage.order_by('quantity')
        elif sort_by == 'price_desc':
            wastage = wastage.order_by('profit_loss')  # Sort by actual loss value (absolute)
        elif sort_by == 'price_asc':
            wastage = wastage.order_by('-profit_loss')  # Reversed since profit_loss is negative
        else:
            wastage = wastage.order_by('-transaction_date')  # Default sort
        
        # Calculate total wastage value - Use profit_loss which properly accounts for product value
        total_wastage = wastage.aggregate(
            total=Sum(Coalesce(F('profit_loss'), 0, output_field=DecimalField()))
        )['total'] or 0
        # The profit_loss is negative, but we want to show a positive value for total wastage
        total_wastage = abs(total_wastage)
        
        # Handle grouping
        grouped_data = None
        
        if group_by:
            # Create a list of groups
            grouped_data = []
            
            # First, group transactions by the group key
            temp_groups = defaultdict(list)
            for transaction in wastage:
                if group_by == 'product':
                    group_key = transaction.product.name
                elif group_by == 'category':
                    group_key = transaction.product.category.name
                elif group_by == 'supplier':
                    group_key = transaction.product.supplier.name if transaction.product.supplier else 'No Supplier'
                elif group_by == 'date':
                    group_key = transaction.transaction_date.strftime('%Y-%m-%d')
                else:
                    group_key = 'Ungrouped'
                
                temp_groups[group_key].append(transaction)
            
            # Then calculate subtotals and create the final structure
            for group_key, transactions in temp_groups.items():
                # Use profit_loss for accurate wastage value (abs to make it positive)
                subtotal = sum(abs(t.profit_loss) for t in transactions)
                grouped_data.append({
                    'name': group_key,
                    'transactions': transactions,
                    'subtotal': subtotal
                })
            
            # Sort the groups if needed
            if sort_by in ('price_desc', 'price_asc'):
                reverse = sort_by == 'price_desc'
                grouped_data.sort(key=lambda x: x['subtotal'], reverse=reverse)
        
        # Ensure start_date and end_date are datetime objects for formatting
        if isinstance(start_date, str):
            start_date_formatted = start_date_obj.strftime('%B %d, %Y')
        else:
            start_date_formatted = start_date.strftime('%B %d, %Y')
            
        if isinstance(end_date, str):
            end_date_formatted = end_date_obj.strftime('%B %d, %Y')
        else:
            end_date_formatted = end_date.strftime('%B %d, %Y')
        
        context = {
            'title': 'Wastage Report',
            'report_title': 'Wastage Report',
            'report_subtitle': f'From {start_date_formatted} to {end_date_formatted}',
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'wastage': wastage,
            'grouped_data': grouped_data,
            'total_wastage': total_wastage,
            'start_date': start_date,
            'end_date': end_date,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'payment':
        # Payment report
        payment_transactions = StockTransaction.objects.filter(
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).exclude(
            payment_status='na'  # Exclude transactions with non-applicable payment status
        ).select_related('product', 'product__category', 'supplier', 'client')
        
        # Apply filters
        if product_id:
            payment_transactions = payment_transactions.filter(product_id=product_id)
        if category_id:
            payment_transactions = payment_transactions.filter(product__category_id=category_id)
        if supplier_id:
            payment_transactions = payment_transactions.filter(supplier_id=supplier_id)
        if client_id:
            payment_transactions = payment_transactions.filter(client_id=client_id)
        
        # Apply payment status filter if provided
        if payment_status:
            payment_transactions = payment_transactions.filter(payment_status=payment_status)
        
        # Apply sorting
        if sort_by == 'date_desc':
            payment_transactions = payment_transactions.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            payment_transactions = payment_transactions.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            payment_transactions = payment_transactions.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            payment_transactions = payment_transactions.order_by('quantity')
        elif sort_by == 'price_desc':
            payment_transactions = payment_transactions.order_by('-total_price')
        elif sort_by == 'price_asc':
            payment_transactions = payment_transactions.order_by('total_price')
        
        # Calculate total amount paid and amount due
        totals = payment_transactions.aggregate(
            total_paid=Sum('amount_paid'),
            total_due=Sum('amount_due')
        )
        total_paid = totals['total_paid'] or 0
        total_due = totals['total_due'] or 0
        
        # Get payment records for the same period
        payment_records = Payment.objects.filter(
            payment_date__gte=start_date_obj,
            payment_date__lte=end_date_obj
        ).select_related('transaction', 'transaction__product', 'created_by')
        
        # Apply transaction filters to payment records
        if payment_transactions:
            payment_records = payment_records.filter(transaction__in=payment_transactions)
        
        # Calculate total payments
        total_payments = payment_records.aggregate(total=Sum('amount'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for transaction in payment_transactions:
                    product_id = transaction.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': transaction.product.name,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    products_dict[product_id]['transactions'].append(transaction)
                    products_dict[product_id]['total_paid'] += transaction.amount_paid
                    products_dict[product_id]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for transaction in payment_transactions:
                    category_id = transaction.product.category_id if transaction.product.category else 0
                    category_name = transaction.product.category.name if transaction.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    categories_dict[category_id]['transactions'].append(transaction)
                    categories_dict[category_id]['total_paid'] += transaction.amount_paid
                    categories_dict[category_id]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for transaction in payment_transactions:
                    supplier_id = transaction.supplier_id if transaction.supplier else 0
                    supplier_name = transaction.supplier.name if transaction.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(transaction)
                    suppliers_dict[supplier_id]['total_paid'] += transaction.amount_paid
                    suppliers_dict[supplier_id]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'client':
                # Group by client
                clients_dict = {}
                for transaction in payment_transactions:
                    client_id = transaction.client_id if transaction.client else 0
                    client_name = transaction.client.name if transaction.client else 'No Client'
                    
                    if client_id not in clients_dict:
                        clients_dict[client_id] = {
                            'name': client_name,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    clients_dict[client_id]['transactions'].append(transaction)
                    clients_dict[client_id]['total_paid'] += transaction.amount_paid
                    clients_dict[client_id]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by name
                for client_id, data in clients_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for transaction in payment_transactions:
                    date_str = transaction.transaction_date.date().strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': date_str,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    dates_dict[date_str]['transactions'].append(transaction)
                    dates_dict[date_str]['total_paid'] += transaction.amount_paid
                    dates_dict[date_str]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
            
            elif group_by == 'payment_status':
                # Group by payment status
                status_dict = {}
                for transaction in payment_transactions:
                    status = transaction.payment_status
                    status_display = dict(StockTransaction.PAYMENT_STATUS_CHOICES).get(status, 'Unknown')
                    
                    if status not in status_dict:
                        status_dict[status] = {
                            'name': status_display,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    status_dict[status]['transactions'].append(transaction)
                    status_dict[status]['total_paid'] += transaction.amount_paid
                    status_dict[status]['total_due'] += transaction.amount_due
                
                # Convert dict to list
                grouped_data = []
                for status, data in status_dict.items():
                    grouped_data.append(data)
                # Sort by status priority: due, partial, credit, paid
                status_priority = {'due': 0, 'partial': 1, 'credit': 2, 'paid': 3}
                grouped_data.sort(key=lambda x: status_priority.get(x['transactions'][0].payment_status, 99))
        
        context.update({
            'report_title': 'Payment Report',
            'payment_transactions': payment_transactions,
            'payment_records': payment_records,
            'total_paid': total_paid,
            'total_due': total_due,
            'total_payments': total_payments,
            'grouped_data': grouped_data,
        })
    
    else:
        context = {
            'report_type': 'unknown',
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    # Render the reports template
    return render(request, 'inventory/reports.html', context)

@login_required
def customize_pdf(request):
    """
    Handle PDF customization and redirect to appropriate PDF generation view
    """
    if request.method == 'POST':
        # Store customization in session
        pdf_customization = {
            'company_name': request.POST.get('company_name', 'QBITX IMS'),
            'company_tagline': request.POST.get('company_tagline', 'Transform Suppliers'),
            'company_details': request.POST.get('company_details', ''),
            'terms_conditions': request.POST.get('terms_conditions', ''),
        }
        request.session['pdf_customization'] = pdf_customization
        
        # Determine PDF type and redirect accordingly
        pdf_type = request.POST.get('pdf_type')
        item_id = request.POST.get('item_id')
        
        if pdf_type == 'invoice' and item_id:
            return redirect('generate_invoice_pdf', invoice_id=item_id)
        elif pdf_type == 'report' and item_id:
            # Build query params from all POST data except those used for customization
            query_params = {}
            for key, value in request.POST.items():
                if key not in ['pdf_type', 'item_id', 'company_name', 'company_tagline', 
                               'company_details', 'terms_conditions', 'csrfmiddlewaretoken']:
                    query_params[key] = value
            
            # Create URL with query parameters
            url = reverse('generate_report_pdf', kwargs={'report_type': item_id})
            if query_params:
                url += '?' + urlencode(query_params)
            return redirect(url)
    
    # If not a POST request or missing data, redirect to dashboard
    return redirect('dashboard')

@view_reports_required
def generate_report_pdf(request, report_type):
    """
    Generate a PDF report based on the report type
    """
    # Get customization from session or use defaults
    customization = request.session.get('pdf_customization', {
        'company_name': 'QBITX IMS',
        'company_tagline': 'Transform Suppliers',
        'company_details': '123 Business Street, Business City, Country',
        'terms_conditions': '',
    })
    
    # Use the report_type parameter to get the context
    all_products = Product.objects.all().order_by('name')
    all_categories = Category.objects.all().order_by('name')
    all_suppliers = Supplier.objects.all().order_by('name')
    all_clients = Client.objects.all().order_by('name')
    
    today = timezone.now().date()
    
    # Get filter parameters from URL
    product_id = request.GET.get('product_id')
    category_id = request.GET.get('category_id')
    supplier_id = request.GET.get('supplier_id')
    client_id = request.GET.get('client_id')
    group_by = request.GET.get('group_by')
    sort_by = request.GET.get('sort_by', 'date_desc')
    payment_status = request.GET.get('payment_status')
    
    # Track applied filters for display
    applied_filters = []
    
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        applied_filters.append(f"Product: {product.name}")
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        applied_filters.append(f"Category: {category.name}")
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id)
        applied_filters.append(f"Supplier: {supplier.name}")
    if client_id:
        client = get_object_or_404(Client, id=client_id)
        applied_filters.append(f"Client: {client.name}")
    if payment_status and report_type == 'payment':
        payment_status_display = dict(StockTransaction.PAYMENT_STATUS_CHOICES).get(payment_status, 'Unknown')
        applied_filters.append(f"Payment Status: {payment_status_display}")
    
    # Set default date range if not provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = today.strftime('%Y-%m-%d')
    
    # Convert string dates to datetime objects
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = today - timedelta(days=30)
        end_date_obj = today
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # Create a context dictionary with the common report data
    context = {
        'report_type': report_type,
        'start_date': start_date_obj,
        'end_date': end_date_obj,
        'today': today,
        'report_title': f"{report_type.title()} Report",
        'report_subtitle': f"From {start_date_obj.strftime('%B %d, %Y')} to {end_date_obj.strftime('%B %d, %Y')}",
        'generation_date': today.strftime("%B %d, %Y"),
        'company_name': customization.get('company_name'),
        'company_tagline': customization.get('company_tagline'),
        'company_details': customization.get('company_details'),
        'terms_conditions': customization.get('terms_conditions'),
        'applied_filters': ', '.join(applied_filters) if applied_filters else None,
    }
    
    # Generate report data based on type
    if report_type == 'inventory':
        # Inventory value report
        products = Product.objects.all()
        
        # Apply filters
        if product_id:
            products = products.filter(id=product_id)
        if category_id:
            products = products.filter(category_id=category_id)
        if supplier_id:
            products = products.filter(supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'quantity_desc':
            products = products.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            products = products.order_by('quantity')
        elif sort_by == 'price_desc':
            products = products.order_by('-buying_price')
        elif sort_by == 'price_asc':
            products = products.order_by('buying_price')
        else:
            products = products.order_by('name')  # Default sort
        
        # Calculate total value for each product
        for product in products:
            product.total_value = product.quantity * product.buying_price
        
        total_value = sum(p.total_value for p in products)
        total_quantity = sum(p.quantity for p in products)
        
        context.update({
            'products': products,
            'total_value': total_value,
            'total_quantity': total_quantity,
        })
    
    elif report_type == 'sales':
        # Sales report
        sales = StockTransaction.objects.filter(
            transaction_type='out',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).select_related('product', 'product__category', 'product__supplier', 'client')
        
        # Apply filters
        if product_id:
            sales = sales.filter(product_id=product_id)
        if category_id:
            sales = sales.filter(product__category_id=category_id)
        if supplier_id:
            sales = sales.filter(product__supplier_id=supplier_id)
        if client_id:
            sales = sales.filter(client_id=client_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            sales = sales.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            sales = sales.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            sales = sales.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            sales = sales.order_by('quantity')
        elif sort_by == 'price_desc':
            sales = sales.order_by('-total_price')
        elif sort_by == 'price_asc':
            sales = sales.order_by('total_price')
        
        # Calculate total sales
        total_sales = sales.aggregate(total=Sum('total_price'))['total'] or 0
        total_quantity_sold = sales.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for sale in sales:
                    product_id = sale.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': sale.product.name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    products_dict[product_id]['transactions'].append(sale)
                    products_dict[product_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for sale in sales:
                    category_id = sale.product.category_id if sale.product.category else 0
                    category_name = sale.product.category.name if sale.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    categories_dict[category_id]['transactions'].append(sale)
                    categories_dict[category_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for sale in sales:
                    supplier_id = sale.product.supplier_id if sale.product.supplier else 0
                    supplier_name = sale.product.supplier.name if sale.product.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(sale)
                    suppliers_dict[supplier_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'client':
                # Group by client
                clients_dict = {}
                for sale in sales:
                    client_id = sale.client_id if sale.client else 0
                    client_name = sale.client.name if sale.client else 'No Client'
                    
                    if client_id not in clients_dict:
                        clients_dict[client_id] = {
                            'name': client_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    clients_dict[client_id]['transactions'].append(sale)
                    clients_dict[client_id]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by name
                for client_id, data in clients_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for sale in sales:
                    date_str = sale.transaction_date.strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': sale.transaction_date.strftime('%B %d, %Y'),
                            'transactions': [],
                            'subtotal': 0
                        }
                    dates_dict[date_str]['transactions'].append(sale)
                    dates_dict[date_str]['subtotal'] += sale.total_price
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
        
        context.update({
            'sales': sales,
            'total_sales': total_sales,
            'total_quantity_sold': total_quantity_sold,
            'grouped_data': grouped_data,
        })
    
    elif report_type == 'purchase':
        # Purchase report (stock in transactions)
        purchases = StockTransaction.objects.filter(
            transaction_type='in',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).select_related('product', 'product__category', 'product__supplier')
        
        # Apply filters
        if product_id:
            purchases = purchases.filter(product_id=product_id)
        if category_id:
            purchases = purchases.filter(product__category_id=category_id)
        if supplier_id:
            purchases = purchases.filter(product__supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            purchases = purchases.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            purchases = purchases.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            purchases = purchases.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            purchases = purchases.order_by('quantity')
        elif sort_by == 'price_desc':
            purchases = purchases.order_by('-total_price')
        elif sort_by == 'price_asc':
            purchases = purchases.order_by('total_price')
        
        # Calculate total purchases
        total_purchases = purchases.aggregate(total=Sum('total_price'))['total'] or 0
        total_quantity_purchased = purchases.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for purchase in purchases:
                    product_id = purchase.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': purchase.product.name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    products_dict[product_id]['transactions'].append(purchase)
                    products_dict[product_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for purchase in purchases:
                    category_id = purchase.product.category_id if purchase.product.category else 0
                    category_name = purchase.product.category.name if purchase.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    categories_dict[category_id]['transactions'].append(purchase)
                    categories_dict[category_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for purchase in purchases:
                    supplier_id = purchase.product.supplier_id if purchase.product.supplier else 0
                    supplier_name = purchase.product.supplier.name if purchase.product.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(purchase)
                    suppliers_dict[supplier_id]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for purchase in purchases:
                    date_str = purchase.transaction_date.strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': purchase.transaction_date.strftime('%B %d, %Y'),
                            'transactions': [],
                            'subtotal': 0
                        }
                    dates_dict[date_str]['transactions'].append(purchase)
                    dates_dict[date_str]['subtotal'] += purchase.total_price
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
        
        # Ensure start_date and end_date are datetime objects for formatting
        if isinstance(start_date, str):
            start_date_formatted = start_date_obj.strftime('%b %d, %Y')
        else:
            start_date_formatted = start_date.strftime('%b %d, %Y')
            
        if isinstance(end_date, str):
            end_date_formatted = end_date_obj.strftime('%b %d, %Y')
        else:
            end_date_formatted = end_date.strftime('%b %d, %Y')
        
        context = {
            'title': 'Purchase Report',
            'report_title': 'Purchase Report',
            'report_subtitle': f"From {start_date_formatted} to {end_date_formatted}",
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'purchases': purchases,
            'grouped_data': grouped_data,
            'total_purchases': total_purchases,
            'total_quantity_purchased': total_quantity_purchased,
            'start_date': start_date,
            'end_date': end_date,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'wastage':
        # Wastage report
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Add date range to applied filters
        applied_filters.append(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get wastage transactions 
        wastage = StockTransaction.objects.filter(
            transaction_type='wastage',  # Focus only on actual wastage transactions
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Apply additional filters
        if product_id:
            wastage = wastage.filter(product_id=product_id)
        if category_id:
            wastage = wastage.filter(product__category_id=category_id)
        if supplier_id:
            wastage = wastage.filter(product__supplier_id=supplier_id)
        
        # Apply sorting
        if sort_by == 'date_desc':
            wastage = wastage.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            wastage = wastage.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            wastage = wastage.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            wastage = wastage.order_by('quantity')
        elif sort_by == 'price_desc':
            wastage = wastage.order_by('profit_loss')  # Sort by actual loss value (absolute)
        elif sort_by == 'price_asc':
            wastage = wastage.order_by('-profit_loss')  # Reversed since profit_loss is negative
        else:
            wastage = wastage.order_by('-transaction_date')  # Default sort
        
        # Calculate total wastage value - Use profit_loss which properly accounts for product value
        total_wastage = wastage.aggregate(
            total=Sum(Coalesce(F('profit_loss'), 0, output_field=DecimalField()))
        )['total'] or 0
        # The profit_loss is negative, but we want to show a positive value for total wastage
        total_wastage = abs(total_wastage)
        
        # Handle grouping
        grouped_data = None
        
        if group_by:
            # Create a list of groups
            grouped_data = []
            
            # First, group transactions by the group key
            temp_groups = defaultdict(list)
            for transaction in wastage:
                if group_by == 'product':
                    group_key = transaction.product.name
                elif group_by == 'category':
                    group_key = transaction.product.category.name
                elif group_by == 'supplier':
                    group_key = transaction.product.supplier.name if transaction.product.supplier else 'No Supplier'
                elif group_by == 'date':
                    group_key = transaction.transaction_date.strftime('%Y-%m-%d')
                else:
                    group_key = 'Ungrouped'
                
                temp_groups[group_key].append(transaction)
            
            # Then calculate subtotals and create the final structure
            for group_key, transactions in temp_groups.items():
                # Use profit_loss for accurate wastage value (abs to make it positive)
                subtotal = sum(abs(t.profit_loss) for t in transactions)
                grouped_data.append({
                    'name': group_key,
                    'transactions': transactions,
                    'subtotal': subtotal
                })
            
            # Sort the groups if needed
            if sort_by in ('price_desc', 'price_asc'):
                reverse = sort_by == 'price_desc'
                grouped_data.sort(key=lambda x: x['subtotal'], reverse=reverse)
        
        # Ensure start_date and end_date are datetime objects for formatting
        if isinstance(start_date, str):
            start_date_formatted = start_date_obj.strftime('%B %d, %Y')
        else:
            start_date_formatted = start_date.strftime('%B %d, %Y')
            
        if isinstance(end_date, str):
            end_date_formatted = end_date_obj.strftime('%B %d, %Y')
        else:
            end_date_formatted = end_date.strftime('%B %d, %Y')
        
        context = {
            'title': 'Wastage Report',
            'report_title': 'Wastage Report',
            'report_subtitle': f'From {start_date_formatted} to {end_date_formatted}',
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'wastage': wastage,
            'grouped_data': grouped_data,
            'total_wastage': total_wastage,
            'start_date': start_date,
            'end_date': end_date,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'payment':
        # Payment report
        payment_transactions = StockTransaction.objects.filter(
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        ).exclude(
            payment_status='na'  # Exclude transactions with non-applicable payment status
        ).select_related('product', 'product__category', 'supplier', 'client')
        
        # Apply filters
        if product_id:
            payment_transactions = payment_transactions.filter(product_id=product_id)
        if category_id:
            payment_transactions = payment_transactions.filter(product__category_id=category_id)
        if supplier_id:
            payment_transactions = payment_transactions.filter(supplier_id=supplier_id)
        if client_id:
            payment_transactions = payment_transactions.filter(client_id=client_id)
        
        # Apply payment status filter if provided
        if payment_status:
            payment_transactions = payment_transactions.filter(payment_status=payment_status)
        
        # Apply sorting
        if sort_by == 'date_desc':
            payment_transactions = payment_transactions.order_by('-transaction_date')
        elif sort_by == 'date_asc':
            payment_transactions = payment_transactions.order_by('transaction_date')
        elif sort_by == 'quantity_desc':
            payment_transactions = payment_transactions.order_by('-quantity')
        elif sort_by == 'quantity_asc':
            payment_transactions = payment_transactions.order_by('quantity')
        elif sort_by == 'price_desc':
            payment_transactions = payment_transactions.order_by('-total_price')
        elif sort_by == 'price_asc':
            payment_transactions = payment_transactions.order_by('total_price')
        
        # Calculate total amount paid and amount due
        totals = payment_transactions.aggregate(
            total_paid=Sum('amount_paid'),
            total_due=Sum('amount_due')
        )
        total_paid = totals['total_paid'] or 0
        total_due = totals['total_due'] or 0
        
        # Get payment records for the same period
        payment_records = Payment.objects.filter(
            payment_date__gte=start_date_obj,
            payment_date__lte=end_date_obj
        ).select_related('transaction', 'transaction__product', 'created_by')
        
        # Apply transaction filters to payment records
        if payment_transactions:
            payment_records = payment_records.filter(transaction__in=payment_transactions)
        
        # Calculate total payments
        total_payments = payment_records.aggregate(total=Sum('amount'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for transaction in payment_transactions:
                    product_id = transaction.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': transaction.product.name,
                            'transactions': [],
                            'total_paid': 0,
                            'total_due': 0
                        }
                    products_dict[product_id]['transactions'].append(transaction)
                    products_dict[product_id]['total_paid'] += transaction.amount_paid
                    products_dict[product_id]['total_due'] += transaction.amount_due
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            # Add other grouping options from reports view if needed
        
        context.update({
            'payment_transactions': payment_transactions,
            'payment_records': payment_records,
            'total_paid': total_paid,
            'total_due': total_due,
            'total_payments': total_payments,
            'grouped_data': grouped_data,
        })
    
    # Generate the PDF using the context
    pdf = render_to_pdf('inventory/pdf/report_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"{report_type}_report_{today.strftime('%Y%m%d')}.pdf"
        content = f"inline; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return redirect('reports')

@view_invoices_required
def generate_invoice_pdf(request, invoice_id):
    """
    Generate a PDF for a specific invoice
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Get customization from session or use defaults
    customization = request.session.get('pdf_customization', {
        'company_name': 'QBITX IMS',
        'company_tagline': 'Transform Suppliers',
        'company_details': '123 Business Street, Business City, Country',
        'terms_conditions': '',
    })
    
    context = {
        'invoice': invoice,
        'company_name': customization.get('company_name'),
        'company_tagline': customization.get('company_tagline'),
        'company_details': customization.get('company_details'),
        'terms_conditions': customization.get('terms_conditions'),
    }
    
    # Render PDF
    pdf = render_to_pdf('inventory/pdf/invoice_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        content = f"inline; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return redirect('invoice_detail', pk=invoice_id)

@view_invoices_required
def invoices(request):
    invoices_list = Invoice.objects.all().order_by('-issue_date')
    
    # Filter by status if specified
    status = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    if status:
        invoices_list = invoices_list.filter(status=status)
    
    if search_query:
        invoices_list = invoices_list.filter(
            Q(invoice_number__icontains=search_query) | 
            Q(client__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(invoices_list, 10)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)
    
    context = {
        'invoices': invoices,
        'status': status,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/invoices.html', context)

@add_invoices_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            # Initialize calculated fields with default values
            invoice.subtotal = 0
            invoice.tax_amount = 0
            invoice.total = 0
            invoice.save()
            
            formset = InvoiceItemFormSet(request.POST, instance=invoice)
            if formset.is_valid():
                formset.save()
                
                # Calculate totals
                subtotal = 0
                for item in invoice.items.all():
                    subtotal += item.total_price
                
                tax_amount = subtotal * (invoice.tax_rate / 100)
                total = subtotal + tax_amount - invoice.discount
                
                invoice.subtotal = subtotal
                invoice.tax_amount = tax_amount
                invoice.total = total
                invoice.save()
                
                messages.success(request, f'Invoice #{invoice.invoice_number} created successfully.')
                return redirect('invoices')
            else:
                # If formset is invalid, we need to keep the invoice for the template
                # but roll back the transaction in the database
                invoice_id = invoice.id
                invoice.delete()
                messages.error(request, 'Please correct the errors in the invoice items.')
                formset = InvoiceItemFormSet()  # Reset formset
        else:
            # If form is invalid, initialize an empty formset
            formset = InvoiceItemFormSet()
            messages.error(request, 'Please correct the errors in the invoice form.')
    else:
        # Generate next invoice number
        last_invoice = Invoice.objects.order_by('-id').first()
        next_number = 1
        if last_invoice:
            try:
                next_number = int(last_invoice.invoice_number) + 1
            except ValueError:
                next_number = 1
        
        form = InvoiceForm(initial={
            'invoice_number': f'{next_number:06d}',
            'issue_date': timezone.now().date(),
            'due_date': timezone.now().date() + timedelta(days=30),
            'tax_rate': 0,
            'discount': 0,
            'subtotal': 0,  # Initialize with default values
        })
        formset = InvoiceItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    
    return render(request, 'inventory/invoice_form.html', context)

@view_invoices_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'inventory/invoice_detail.html', context)

@login_required
def warehouse_create_ajax(request):
    """Create a new warehouse via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            location = data.get('location')
            description = data.get('description')
            is_active = data.get('is_active', True)
            
            if not name or not location:
                return JsonResponse({'success': False, 'error': 'Name and location are required'})
            
            warehouse = Warehouse.objects.create(
                name=name,
                location=location,
                description=description,
                is_active=is_active
            )
            
            return JsonResponse({
                'success': True,
                'warehouse': {
                    'id': warehouse.id,
                    'name': warehouse.name,
                    'location': warehouse.location
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def product_duplicate(request, pk):
    """Duplicate a product with variations"""
    original_product = get_object_or_404(Product, pk=pk)
    
    # Get filter parameters to preserve them after redirect
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    page = request.GET.get('page')
    
    # Build redirect URL parameters for products page
    products_redirect_params = {}
    if category_id:
        products_redirect_params['category'] = category_id
    if search_query:
        products_redirect_params['search'] = search_query
    if page:
        products_redirect_params['page'] = page
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        sku = request.POST.get('sku')
        copy_quantity = request.POST.get('copy_quantity') == 'on'
        warehouse_id = request.POST.get('warehouse')
        
        # Validate form data
        if not name or not sku:
            messages.error(request, 'Name and SKU are required')
            if products_redirect_params:
                redirect_url = reverse('products') + '?' + urlencode(products_redirect_params)
                return redirect(redirect_url)
            return redirect('products')
        
        # Check if SKU already exists in the same warehouse
        warehouse = None
        if warehouse_id:
            warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
        
        if Product.objects.filter(sku=sku, warehouse=warehouse).exists():
            messages.error(request, f'SKU {sku} already exists in the selected warehouse')
            if products_redirect_params:
                redirect_url = reverse('products') + '?' + urlencode(products_redirect_params)
                return redirect(redirect_url)
            return redirect('products')
        
        # Create new product as a copy of the original
        new_product = Product.objects.create(
            name=name,
            sku=sku,
            category=original_product.category,
            description=original_product.description,
            buying_price=original_product.buying_price,
            selling_price=original_product.selling_price,
            unit_of_measure=original_product.unit_of_measure,
            quantity=original_product.quantity if copy_quantity else 0,
            reorder_level=original_product.reorder_level,
            shipment_number=original_product.shipment_number,
            warehouse=warehouse,
            expiry_date=original_product.expiry_date,
            supplier=original_product.supplier
        )
        
        messages.success(request, f'Product "{original_product.name}" duplicated successfully as "{name}"')
        
        # Add the filter parameters to the product_edit URL
        edit_redirect_params = products_redirect_params.copy()
        edit_url = reverse('product_edit', kwargs={'pk': new_product.id})
        if edit_redirect_params:
            edit_url += '?' + urlencode(edit_redirect_params)
        return redirect(edit_url)
    
    # If not POST, redirect back to products with preserved filters
    if products_redirect_params:
        redirect_url = reverse('products') + '?' + urlencode(products_redirect_params)
        return redirect(redirect_url)
    return redirect('products')

@login_required
def payments(request):
    """View all payments and filter them"""
    # Get filter parameters
    payment_status = request.GET.get('payment_status')
    client_id = request.GET.get('client_id')
    supplier_id = request.GET.get('supplier_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    transaction_type = request.GET.get('transaction_type')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    transactions = StockTransaction.objects.exclude(payment_status='na').order_by('-transaction_date')
    
    # Apply filters
    if payment_status:
        # Handle comma-separated payment statuses
        if ',' in payment_status:
            status_list = payment_status.split(',')
            transactions = transactions.filter(payment_status__in=status_list)
        else:
            transactions = transactions.filter(payment_status=payment_status)
    
    if client_id:
        transactions = transactions.filter(client_id=client_id)
    if supplier_id:
        transactions = transactions.filter(supplier_id=supplier_id)
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Date range filter
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__gte=start_date_obj)
        except ValueError:
            pass
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # Search filter
    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(product__name__icontains=search_query) | 
            Q(reference_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    # Get payment records for display
    payment_records = Payment.objects.all().order_by('-payment_date')
    
    # Get reference data for filtering
    all_clients = Client.objects.all().order_by('name')
    all_suppliers = Supplier.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(transactions, 10)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)
    
    context = {
        'transactions': transactions_page,
        'payment_records': payment_records,
        'all_clients': all_clients,
        'all_suppliers': all_suppliers,
        'payment_status': payment_status,
        'client_id': int(client_id) if client_id else None,
        'supplier_id': int(supplier_id) if supplier_id else None,
        'transaction_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/payments.html', context)

@login_required
def payment_create(request):
    """Create a new payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        
        # Get the transaction ID from the hidden field
        transaction_id = request.POST.get('transaction')
        if transaction_id:
            try:
                transaction = StockTransaction.objects.get(pk=transaction_id)
                
                # Create a payment instance but don't save yet
                payment = form.save(commit=False)
                payment.transaction = transaction
                payment.created_by = request.user
                payment.save()
                
                messages.success(request, f'Payment of {payment.amount} recorded successfully. Transaction status is now {transaction.get_payment_status_display()}.')
                return redirect('payments')
            except StockTransaction.DoesNotExist:
                messages.error(request, 'Transaction not found.')
                return redirect('payment_create')
        else:
            # If no transaction ID is provided, validate the form normally
            if form.is_valid():
                payment = form.save(commit=False)
                payment.created_by = request.user
                payment.save()
                
                # Get updated transaction info
                transaction = payment.transaction
                
                messages.success(request, f'Payment of {payment.amount} recorded successfully. Transaction status is now {transaction.get_payment_status_display()}.')
                return redirect('payments')
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'title': 'Record Payment'
    }
    
    return render(request, 'inventory/payment_form.html', context)

@login_required
def payment_for_transaction(request, transaction_id):
    """Add a payment for a specific transaction"""
    transaction = get_object_or_404(StockTransaction, pk=transaction_id)
    
    # Redirect if transaction is already fully paid
    if transaction.payment_status == 'paid':
        messages.info(request, f'This transaction is already fully paid.')
        return redirect('payments')
    
    if request.method == 'POST':
        # Prepopulate the form with the transaction
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.transaction = transaction
            payment.created_by = request.user
            payment.save()
            
            messages.success(request, f'Payment of {payment.amount} recorded successfully. Transaction status is now {transaction.get_payment_status_display()}.')
            return redirect('payments')
    else:
        # Pre-fill the form with the transaction and suggested amount (remaining due amount)
        initial_data = {
            'transaction': transaction,
            'amount': transaction.amount_due,
            'payment_date': timezone.now().date(),
        }
        form = PaymentForm(initial=initial_data)
        # Disable the transaction field since we're paying for a specific transaction
        form.fields['transaction'].disabled = True
    
    context = {
        'form': form,
        'transaction': transaction,
        'title': f'Record Payment for {transaction.product.name}'
    }
    
    return render(request, 'inventory/payment_form.html', context)

@login_required
def generate_invoice_from_transaction(request, transaction_id):
    """Generate an invoice from a stock transaction"""
    transaction = get_object_or_404(StockTransaction, pk=transaction_id)
    
    # Only allow generating invoices for 'out' transactions with a client
    if transaction.transaction_type != 'out' or not transaction.client:
        messages.error(request, 'Invoices can only be generated for stock out transactions with a client.')
        return redirect('stock')
    
    if request.method == 'POST':
        try:
            # Check if an invoice already exists for this transaction
            reference_number = f"TRANS-{transaction.id}"
            existing_invoice = Invoice.objects.filter(notes__contains=reference_number).first()
            
            if existing_invoice:
                messages.info(request, f'An invoice (#{existing_invoice.invoice_number}) already exists for this transaction.')
                
                # Redirect to the invoice detail page or generate PDF directly
                if request.POST.get('generate_pdf', False):
                    return redirect('generate_invoice_pdf', invoice_id=existing_invoice.id)
                else:
                    return redirect('invoice_detail', pk=existing_invoice.id)
            
            # Generate next invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            next_number = 1
            if last_invoice:
                try:
                    next_number = int(last_invoice.invoice_number) + 1
                except ValueError:
                    next_number = 1
            
            # Create the invoice
            invoice = Invoice.objects.create(
                invoice_number=f'{next_number:06d}',
                client=transaction.client,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30),
                status='pending' if transaction.payment_status in ['due', 'partial', 'credit'] else 'paid',
                subtotal=transaction.total_price,
                tax_rate=transaction.vat_rate + transaction.ait_rate if transaction.apply_taxes else 0,
                tax_amount=transaction.total_price - (transaction.quantity * transaction.final_price) if transaction.apply_taxes and transaction.final_price else 0,
                discount=0,
                total=transaction.total_price,
                notes=f"{reference_number} - Generated from transaction #{transaction.id} on {timezone.now().strftime('%Y-%m-%d')}",
                created_by=request.user
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                product=transaction.product,
                quantity=transaction.quantity,
                unit_price=transaction.unit_price,
                total_price=transaction.total_price
            )
            
            messages.success(request, f'Invoice #{invoice.invoice_number} created successfully.')
            
            # Redirect to the invoice detail page or generate PDF directly
            if request.POST.get('generate_pdf', False):
                return redirect('generate_invoice_pdf', invoice_id=invoice.id)
            else:
                return redirect('invoice_detail', pk=invoice.id)
                
        except Exception as e:
            messages.error(request, f'Error generating invoice: {str(e)}')
            return redirect('stock')
    
    # If not POST, redirect back to stock page
    return redirect('stock')

@login_required
def get_transaction_details(request, transaction_id):
    """API endpoint to get transaction details by ID"""
    try:
        transaction = get_object_or_404(StockTransaction, pk=transaction_id)
        
        # Create response data
        data = {
            'id': transaction.id,
            'transaction_id': transaction.transaction_id,
            'product_id': transaction.product_id,
            'product_name': transaction.product.name,
            'transaction_type': transaction.transaction_type,
            'transaction_type_display': transaction.get_transaction_type_display(),
            'transaction_date': transaction.transaction_date.isoformat(),
            'quantity': transaction.quantity,
            'buying_price': float(transaction.buying_price),
            'selling_price': float(transaction.selling_price),
            'unit_price': float(transaction.unit_price),
            'total_price': float(transaction.total_price),
            'payment_status': transaction.payment_status,
            'payment_status_display': transaction.get_payment_status_display(),
            'amount_paid': float(transaction.amount_paid),
            'amount_due': float(transaction.amount_due),
            'reference_number': transaction.reference_number,
            'notes': transaction.notes,
        }
        
        # Add client or supplier info if available
        if transaction.client:
            data['client_id'] = transaction.client_id
            data['client_name'] = transaction.client.name
        
        if transaction.supplier:
            data['supplier_id'] = transaction.supplier_id
            data['supplier_name'] = transaction.supplier.name
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

@login_required
def category_create_ajax(request):
    """Create a new category via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            icon = data.get('icon')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'})
            
            category = Category.objects.create(
                name=name,
                icon=icon
            )
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def supplier_create_ajax(request):
    """Create a new supplier via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            contact_person = data.get('contact_person')
            email = data.get('email')
            phone = data.get('phone')
            address = data.get('address')
            city = data.get('city')
            country = data.get('country')
            notes = data.get('notes')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'})
            
            supplier = Supplier.objects.create(
                name=name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                address=address,
                city=city,
                country=country,
                notes=notes
            )
            
            return JsonResponse({
                'success': True,
                'supplier': {
                    'id': supplier.id,
                    'name': supplier.name
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def client_create_ajax(request):
    """Create a new client via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            contact_person = data.get('contact_person')
            email = data.get('email')
            phone = data.get('phone')
            address = data.get('address')
            city = data.get('city')
            country = data.get('country')
            notes = data.get('notes')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'})
            
            client = Client.objects.create(
                name=name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                address=address,
                city=city,
                country=country,
                notes=notes
            )
            
            return JsonResponse({
                'success': True,
                'client': {
                    'id': client.id,
                    'name': client.name
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def invoice_delete(request, pk):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice #{invoice_number} deleted successfully.')
        return redirect('invoices')
    
    # If not POST, redirect back to invoices
    return redirect('invoices')

@login_required
def stock_transaction_delete(request, pk):
    """Delete a stock transaction"""
    transaction = get_object_or_404(StockTransaction, pk=pk)
    
    if request.method == 'POST':
        # Store transaction info for success message
        transaction_id = transaction.transaction_id
        product_name = transaction.product.name
        
        # Check if this transaction has an associated invoice
        reference_number = f"TRANS-{transaction.id}"
        invoice = Invoice.objects.filter(notes__contains=reference_number).first()
        
        # If there's an associated invoice, delete it first
        if invoice:
            invoice.delete()
        
        # Revert the product quantity changes
        product = transaction.product
        if transaction.transaction_type == 'in' or transaction.transaction_type == 'return':
            # If it was stock in, reduce the quantity
            product.quantity -= transaction.quantity
        elif transaction.transaction_type == 'out' or transaction.transaction_type == 'wastage':
            # If it was stock out or wastage, add the quantity back
            product.quantity += transaction.quantity
        
        # Save the product with updated quantity
        product.save()
        
        # Delete the transaction
        transaction.delete()
        
        messages.success(request, f'Transaction {transaction_id} for {product_name} deleted successfully.')
        
        # Redirect back to stock page
        return redirect('stock')
    
    # If not POST, redirect back to stock
    return redirect('stock')
