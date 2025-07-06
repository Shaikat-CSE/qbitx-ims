from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
from django.urls import reverse
from urllib.parse import urlencode

from .models import Product, Category, Supplier, Client, StockTransaction, Invoice
from .forms import (
    ProductForm, CategoryForm, SupplierForm, ClientForm, 
    StockTransactionForm, InvoiceForm, InvoiceItemFormSet
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
    
    context = {
        'today': today,
        'total_products': total_products,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'total_wastage': total_wastage,
        'top_products': top_products,
        'top_products_labels': json.dumps(top_products_labels),
        'top_products_values': json.dumps(sales_values),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'sales_dates': json.dumps(sales_dates),
        'sales_values': json.dumps(sales_values),
    }
    
    return render(request, 'inventory/dashboard.html', context)

@view_products_required
def products(request):
    categories = Category.objects.all()
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    products_list = Product.objects.all().order_by('id')  # Add default ordering
    
    if category_id:
        products_list = products_list.filter(category_id=category_id)
    
    if search_query:
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
            })
        return JsonResponse(products_data, safe=False)
    
    # Pagination
    paginator = Paginator(products_list, 10)  # Show 10 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/products.html', context)

@add_products_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully.')
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
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully.')
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
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully.')
        return redirect('products')
    
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
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    transactions_list = StockTransaction.objects.all().order_by('-transaction_date')
    
    # Apply filters
    if transaction_type:
        transactions_list = transactions_list.filter(transaction_type=transaction_type)
    
    if product_id:
        transactions_list = transactions_list.filter(product_id=product_id)
    
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
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'inventory/stock.html', context)

@add_stock_required
def stock_create(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            
            # Set unit_price based on transaction type
            if transaction.transaction_type == 'out':
                transaction.unit_price = transaction.selling_price
            else:
                transaction.unit_price = transaction.buying_price
            
            transaction.save()
            messages.success(request, f'Stock transaction created successfully.')
            return redirect('stock')
    else:
        form = StockTransactionForm(initial={'transaction_date': timezone.now()})
    
    context = {
        'form': form,
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
    
    # Get report type
    report_type = request.GET.get('type', 'inventory')
    
    # Get filter parameters
    product_id = request.GET.get('product_id')
    category_id = request.GET.get('category_id')
    supplier_id = request.GET.get('supplier_id')
    client_id = request.GET.get('client_id')
    group_by = request.GET.get('group_by')
    sort_by = request.GET.get('sort_by', 'date_desc')
    
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
        
        context.update({
            'report_title': 'Inventory Value Report',
            'products': products,
            'total_value': total_value,
        })
    
    elif report_type == 'sales':
        # Sales report
        sales = StockTransaction.objects.filter(
            transaction_type='out',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        )
        
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
            'grouped_data': grouped_data,
        })
    
    elif report_type == 'purchase':
        # Purchase report (stock in transactions)
        purchases = StockTransaction.objects.filter(
            transaction_type='in',
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        )
        
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
        
        context.update({
            'report_title': 'Purchase Report',
            'purchases': purchases,
            'total_purchases': total_purchases,
            'grouped_data': grouped_data,
        })
    
    elif report_type == 'wastage':
        # Wastage report
        wastage = StockTransaction.objects.filter(
            Q(transaction_type='wastage') | Q(wastage_amount__gt=0),
            transaction_date__date__gte=start_date_obj,
            transaction_date__date__lte=end_date_obj
        )
        
        # Apply filters
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
            wastage = wastage.order_by('-wastage_amount')
        elif sort_by == 'price_asc':
            wastage = wastage.order_by('wastage_amount')
        
        # Calculate total wastage
        total_wastage = wastage.aggregate(total=Sum('wastage_amount'))['total'] or 0
        
        # Group data if requested
        grouped_data = None
        if group_by:
            grouped_data = []
            
            if group_by == 'product':
                # Group by product
                products_dict = {}
                for waste in wastage:
                    product_id = waste.product_id
                    if product_id not in products_dict:
                        products_dict[product_id] = {
                            'name': waste.product.name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    products_dict[product_id]['transactions'].append(waste)
                    products_dict[product_id]['subtotal'] += waste.wastage_amount
                
                # Convert dict to list and sort by name
                for product_id, data in products_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'category':
                # Group by category
                categories_dict = {}
                for waste in wastage:
                    category_id = waste.product.category_id if waste.product.category else 0
                    category_name = waste.product.category.name if waste.product.category else 'Uncategorized'
                    
                    if category_id not in categories_dict:
                        categories_dict[category_id] = {
                            'name': category_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    categories_dict[category_id]['transactions'].append(waste)
                    categories_dict[category_id]['subtotal'] += waste.wastage_amount
                
                # Convert dict to list and sort by name
                for category_id, data in categories_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'supplier':
                # Group by supplier
                suppliers_dict = {}
                for waste in wastage:
                    supplier_id = waste.product.supplier_id if waste.product.supplier else 0
                    supplier_name = waste.product.supplier.name if waste.product.supplier else 'No Supplier'
                    
                    if supplier_id not in suppliers_dict:
                        suppliers_dict[supplier_id] = {
                            'name': supplier_name,
                            'transactions': [],
                            'subtotal': 0
                        }
                    suppliers_dict[supplier_id]['transactions'].append(waste)
                    suppliers_dict[supplier_id]['subtotal'] += waste.wastage_amount
                
                # Convert dict to list and sort by name
                for supplier_id, data in suppliers_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'])
            
            elif group_by == 'date':
                # Group by date
                dates_dict = {}
                for waste in wastage:
                    date_str = waste.transaction_date.strftime('%Y-%m-%d')
                    
                    if date_str not in dates_dict:
                        dates_dict[date_str] = {
                            'name': waste.transaction_date.strftime('%B %d, %Y'),
                            'transactions': [],
                            'subtotal': 0
                        }
                    dates_dict[date_str]['transactions'].append(waste)
                    dates_dict[date_str]['subtotal'] += waste.wastage_amount
                
                # Convert dict to list and sort by date
                for date_str, data in dates_dict.items():
                    grouped_data.append(data)
                grouped_data.sort(key=lambda x: x['name'], reverse=(sort_by == 'date_desc'))
        
        context.update({
            'report_title': 'Wastage Report',
            'wastage': wastage,
            'total_wastage': total_wastage,
            'grouped_data': grouped_data,
        })
    
    return render(request, 'inventory/reports.html', context)

@view_reports_required
def customize_pdf(request):
    """
    View to handle PDF customization options before generating the PDF
    """
    if request.method == 'POST':
        # Get customization options from the form
        company_name = request.POST.get('company_name', 'QBITX IMS')
        company_tagline = request.POST.get('company_tagline', 'Transform Suppliers')
        company_details = request.POST.get('company_details', '123 Business Street, Business City, Country')
        terms_conditions = request.POST.get('terms_conditions', '')
        
        # Store customization in session for use in PDF generation
        request.session['pdf_customization'] = {
            'company_name': company_name,
            'company_tagline': company_tagline,
            'company_details': company_details,
            'terms_conditions': terms_conditions,
        }
        
        # Redirect to the actual PDF generation based on the type and ID
        pdf_type = request.POST.get('pdf_type')
        item_id = request.POST.get('item_id')
        
        if pdf_type == 'report':
            # Collect all filter parameters
            filter_params = {}
            for key, value in request.POST.items():
                if key not in ['pdf_type', 'item_id', 'company_name', 'company_tagline', 
                              'company_details', 'terms_conditions', 'csrfmiddlewaretoken']:
                    filter_params[key] = value
            
            # Build the redirect URL with query parameters
            url = reverse('generate_report_pdf', kwargs={'report_type': item_id})
            if filter_params:
                url += '?' + urlencode(filter_params)
            
            return redirect(url)
        elif pdf_type == 'invoice':
            return redirect('generate_invoice_pdf', invoice_id=item_id)
    
    # If not a POST request or missing parameters, redirect to dashboard
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
    
    today = timezone.now().date()
    
    # Get all filter parameters
    product_id = request.GET.get('product_id')
    category_id = request.GET.get('category_id')
    supplier_id = request.GET.get('supplier_id')
    client_id = request.GET.get('client_id')
    group_by = request.GET.get('group_by')
    sort_by = request.GET.get('sort_by', 'date_desc')
    
    # Track applied filters for display
    applied_filters = []
    subtitle_parts = []
    
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        applied_filters.append(f"Product: {product.name}")
        subtitle_parts.append(f"Product: {product.name}")
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        applied_filters.append(f"Category: {category.name}")
        subtitle_parts.append(f"Category: {category.name}")
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id)
        applied_filters.append(f"Supplier: {supplier.name}")
        subtitle_parts.append(f"Supplier: {supplier.name}")
    if client_id:
        client = get_object_or_404(Client, id=client_id)
        applied_filters.append(f"Client: {client.name}")
        subtitle_parts.append(f"Client: {client.name}")
    
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
        
        report_subtitle = f'All products as of {today.strftime("%B %d, %Y")}'
        if subtitle_parts:
            report_subtitle += f" ({', '.join(subtitle_parts)})"
        
        context = {
            'title': 'Inventory Value Report',
            'report_title': 'Inventory Value Report',
            'report_subtitle': report_subtitle,
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'products': products,
            'total_value': total_value,
            'today': today,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'sales':
        # Sales report
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Add date range to applied filters
        subtitle_parts.append(f"From {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
        
        sales = StockTransaction.objects.filter(
            transaction_type='out',
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Apply additional filters
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
        else:
            sales = sales.order_by('-transaction_date')  # Default sort
        
        total_sales = sales.aggregate(
            total=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
        )['total'] or 0
        
        # Handle grouping
        grouped_data = None
        
        if group_by:
            # Create a list of tuples (group_name, transactions, subtotal) instead of a dictionary
            grouped_data = []
            
            # First, group transactions by the group key
            temp_groups = defaultdict(list)
            for transaction in sales:
                if group_by == 'product':
                    group_key = transaction.product.name
                elif group_by == 'category':
                    group_key = transaction.product.category.name
                elif group_by == 'supplier':
                    group_key = transaction.product.supplier.name if transaction.product.supplier else 'No Supplier'
                elif group_by == 'client':
                    group_key = transaction.client.name if transaction.client else 'No Client'
                elif group_by == 'date':
                    group_key = transaction.transaction_date.strftime('%Y-%m-%d')
                else:
                    group_key = 'Ungrouped'
                
                temp_groups[group_key].append(transaction)
            
            # Then calculate subtotals and create the final structure
            for group_key, transactions in temp_groups.items():
                subtotal = sum(t.total_price for t in transactions)
                grouped_data.append({
                    'name': group_key,
                    'transactions': transactions,
                    'subtotal': subtotal
                })
            
            # Sort the groups if needed
            if sort_by in ('price_desc', 'price_asc'):
                reverse = sort_by == 'price_desc'
                grouped_data.sort(key=lambda x: x['subtotal'], reverse=reverse)
        
        report_subtitle = f"Sales Report"
        if subtitle_parts:
            report_subtitle += f" ({', '.join(subtitle_parts)})"
        
        context = {
            'title': 'Sales Report',
            'report_title': 'Sales Report',
            'report_subtitle': report_subtitle,
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'sales': sales,
            'grouped_data': grouped_data,
            'total_sales': total_sales,
            'start_date': start_date,
            'end_date': end_date,
            'applied_filters': ', '.join(applied_filters) if applied_filters else None,
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    elif report_type == 'purchase':
        # Purchase report
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
        
        purchases = StockTransaction.objects.filter(
            transaction_type='in',
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Apply additional filters
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
        else:
            purchases = purchases.order_by('-transaction_date')  # Default sort
        
        # Calculate total purchases value
        total_purchases = purchases.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Handle grouping
        grouped_data = None
        
        if group_by:
            # Create a list of groups
            grouped_data = []
            
            # First, group transactions by the group key
            temp_groups = defaultdict(list)
            for transaction in purchases:
                if group_by == 'product':
                    group_key = transaction.product.name
                elif group_by == 'category':
                    group_key = transaction.product.category.name
                elif group_by == 'supplier':
                    group_key = transaction.product.supplier.name if transaction.product.supplier else 'No Supplier'
                elif group_by == 'client':
                    group_key = transaction.client.name if transaction.client else 'No Client'
                elif group_by == 'date':
                    group_key = transaction.transaction_date.strftime('%Y-%m-%d')
                else:
                    group_key = 'Ungrouped'
                
                temp_groups[group_key].append(transaction)
            
            # Then calculate subtotals and create the final structure
            for group_key, transactions in temp_groups.items():
                subtotal = sum(t.total_price for t in transactions)
                grouped_data.append({
                    'name': group_key,
                    'transactions': transactions,
                    'subtotal': subtotal
                })
            
            # Sort the groups if needed
            if sort_by in ('price_desc', 'price_asc'):
                reverse = sort_by == 'price_desc'
                grouped_data.sort(key=lambda x: x['subtotal'], reverse=reverse)
        
        context = {
            'title': 'Purchase Report',
            'report_title': 'Purchase Report',
            'report_subtitle': f"From {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}",
            'generation_date': today.strftime("%B %d, %Y"),
            'report_type': report_type,
            'purchases': purchases,
            'grouped_data': grouped_data,
            'total_purchases': total_purchases,
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
        
        # Get all transactions with wastage amount > 0
        wastage = StockTransaction.objects.filter(
            Q(transaction_type='wastage') | 
            Q(wastage_amount__gt=0),  # Include any transaction with wastage
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
            wastage = wastage.order_by('-wastage_amount')
        elif sort_by == 'price_asc':
            wastage = wastage.order_by('wastage_amount')
        else:
            wastage = wastage.order_by('-transaction_date')  # Default sort
        
        # Calculate total wastage value
        total_wastage = wastage.aggregate(
            total=Sum('wastage_amount')
        )['total'] or 0
        
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
                subtotal = sum(t.wastage_amount for t in transactions)
                grouped_data.append({
                    'name': group_key,
                    'transactions': transactions,
                    'subtotal': subtotal
                })
            
            # Sort the groups if needed
            if sort_by in ('price_desc', 'price_asc'):
                reverse = sort_by == 'price_desc'
                grouped_data.sort(key=lambda x: x['subtotal'], reverse=reverse)
        
        context = {
            'title': 'Wastage Report',
            'report_title': 'Wastage Report',
            'report_subtitle': f'From {start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}',
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
    
    else:
        context = {
            'report_type': 'unknown',
            'company_name': customization.get('company_name'),
            'company_tagline': customization.get('company_tagline'),
            'company_details': customization.get('company_details'),
            'terms_conditions': customization.get('terms_conditions'),
        }
    
    # Generate PDF
    pdf = render_to_pdf('inventory/pdf/report_pdf.html', context)
    if pdf:
        response = pdf
        filename = f"{report_type}_report_{today.strftime('%Y%m%d')}.pdf"
        content = f"attachment; filename={filename}"
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
