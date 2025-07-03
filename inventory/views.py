from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from .models import Product, StockTransaction, ProductType, Supplier, Client
from .serializers import ProductSerializer, StockTransactionSerializer, ProductTypeSerializer, SupplierSerializer, ClientSerializer
from django.db.models import Count, Sum, F, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, BasePermission
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta

# Create your views here.

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        threshold = int(request.query_params.get('threshold', 5))
        products = Product.objects.filter(quantity__lte=threshold)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        total_products = Product.objects.count()
        total_value = Product.objects.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
        low_stock_count = Product.objects.filter(quantity__lte=5).count()
        
        return Response({
            'total_products': total_products,
            'total_value': total_value,
            'low_stock_count': low_stock_count
        })
    
    @action(detail=False, methods=['get'])
    def wastage_stats(self, request):
        # Calculate total wastage value from StockTransaction records
        # where is_wastage=True
        wastage_transactions = StockTransaction.objects.filter(is_wastage=True)
        
        # Sum of quantity * unit_price for all wastage transactions
        total_wastage_value = wastage_transactions.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
        
        # Get total wastage quantity
        total_wastage_qty = wastage_transactions.aggregate(
            total_qty=Sum('quantity')
        )['total_qty'] or 0
        
        # Count of wastage transactions
        wastage_count = wastage_transactions.count()
        
        # Add wastage from Product model
        product_wastage = Product.objects.aggregate(
            total_product_wastage=Sum('wastage')
        )['total_product_wastage'] or 0
        
        # Total wastage is the sum of transaction wastage and product wastage
        total_wastage = total_wastage_value + product_wastage
        
        return Response({
            'total_wastage': total_wastage,
            'transaction_wastage': total_wastage_value,
            'product_wastage': product_wastage,
            'total_wastage_qty': total_wastage_qty,
            'wastage_count': wastage_count
        })

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        supplier = self.get_object()
        transactions = supplier.transactions.all()
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        supplier = self.get_object()
        # Get unique products from transactions
        product_ids = supplier.transactions.values_list('product', flat=True).distinct()
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        client = self.get_object()
        transactions = client.transactions.all()
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        client = self.get_object()
        # Get unique products from transactions
        product_ids = client.transactions.values_list('product', flat=True).distinct()
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class StockHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockTransaction.objects.all().order_by('-date')
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    def retrieve(self, request, pk=None):
        try:
            transaction = StockTransaction.objects.get(pk=pk)
            serializer = self.get_serializer(transaction)
            
            # Add product name to response
            data = serializer.data
            data['product_name'] = transaction.product.name
            
            # Add supplier/client name if available
            if transaction.supplier_ref:
                data['supplier_name'] = transaction.supplier_ref.name
            
            if transaction.client_ref:
                data['client_name'] = transaction.client_ref.name
                
            return Response(data)
        except StockTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=404)

class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class StockUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            product_id = request.data.get('product')
            quantity = int(request.data.get('quantity'))
            transaction_type = request.data.get('type')
            notes = request.data.get('notes', '')
            reference_number = request.data.get('reference_number', '')
            unit_price = request.data.get('unit_price')
            discount = request.data.get('discount', 0)
            supplier = request.data.get('supplier', '')
            supplier_contact = request.data.get('supplier_contact', '')
            client = request.data.get('client', '')
            client_contact = request.data.get('client_contact', '')
            is_wastage = request.data.get('is_wastage', False)
            wastage = request.data.get('wastage', 0)
            
            # Get supplier or client references if IDs are provided
            supplier_ref = None
            client_ref = None
            
            supplier_id = request.data.get('supplier_id')
            client_id = request.data.get('client_id')
            
            if supplier_id:
                try:
                    supplier_ref = Supplier.objects.get(id=supplier_id)
                except Supplier.DoesNotExist:
                    pass
                    
            if client_id:
                try:
                    client_ref = Client.objects.get(id=client_id)
                except Client.DoesNotExist:
                    pass
            
            # Validate inputs
            if not product_id or not quantity or not transaction_type:
                return Response({'error': 'Missing required fields'}, status=400)
                
            if transaction_type not in ['IN', 'OUT']:
                return Response({'error': 'Invalid transaction type'}, status=400)
                
            # Get product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=404)
                
            # For stock out, check if enough quantity is available
            if transaction_type == 'OUT' and product.quantity < quantity:
                return Response({'error': 'Insufficient stock'}, status=400)
                
            # Update product quantity
            if transaction_type == 'IN':
                product.quantity += quantity
            else:
                product.quantity -= quantity
                
            product.save()
            
            # Create stock transaction record
            transaction = StockTransaction.objects.create(
                product=product,
                quantity=quantity,
                type=transaction_type,
                notes=notes,
                reference_number=reference_number,
                unit_price=unit_price,
                discount=discount,
                supplier=supplier,
                supplier_contact=supplier_contact,
                client=client,
                client_contact=client_contact,
                supplier_ref=supplier_ref,
                client_ref=client_ref,
                is_wastage=is_wastage,
                wastage=wastage
            )
            
            # Return updated product info
            return Response({
                'success': True,
                'transaction_id': transaction.id,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'quantity': product.quantity
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

# User permissions view
class UserPermissionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Get all permissions the user has, either directly or through groups
        permissions = []
        
        # Add direct permissions
        for perm in user.user_permissions.all():
            permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
        
        # Add permissions from groups
        for group in user.groups.all():
            for perm in group.permissions.all():
                perm_code = f"{perm.content_type.app_label}.{perm.codename}"
                if perm_code not in permissions:
                    permissions.append(perm_code)
        
        # If user is superuser, add all permissions
        if user.is_superuser:
            all_content_types = ContentType.objects.all()
            for ct in all_content_types:
                for perm in Permission.objects.filter(content_type=ct):
                    perm_code = f"{ct.app_label}.{perm.codename}"
                    if perm_code not in permissions:
                        permissions.append(perm_code)
        
        return Response(permissions)

# Custom permission class for reports
class ReportPermission(BasePermission):
    def has_permission(self, request, view):
        # Check if user has the custom view_reports permission
        if request.method == 'GET':
            return request.user.has_perm('inventory.view_reports')
        # For exporting, need export_reports permission
        elif request.query_params.get('export'):
            return request.user.has_perm('inventory.export_reports')
        return False

# Report view with custom permissions
class ReportsView(APIView):
    permission_classes = [IsAuthenticated, ReportPermission]
    
    def get(self, request):
        """
        Get reports data with filters.
        
        Query params:
        - report_type: 'all', 'sales', 'purchases'
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - product_id: Filter by product ID
        - supplier_id: Filter by supplier ID
        - client_id: Filter by client ID
        - product_type: Filter by product type
        - export: If present, format for export (CSV, PDF)
        """
        try:
            # Get report parameters
            report_type = request.query_params.get('report_type', 'all')
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            product_id = request.query_params.get('product_id')
            supplier_id = request.query_params.get('supplier_id')
            client_id = request.query_params.get('client_id')
            product_type = request.query_params.get('product_type')
            export_format = request.query_params.get('export')
            
            # Base queryset
            queryset = StockTransaction.objects.all()
            
            # Apply report type filter
            if report_type == 'sales':
                queryset = queryset.filter(type='OUT')
            elif report_type == 'purchases':
                queryset = queryset.filter(type='IN')
            
            # Apply date filters if provided
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    queryset = queryset.filter(date__gte=start_date)
                except ValueError:
                    return Response({"error": "Invalid start_date format. Use YYYY-MM-DD"}, status=400)
            
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    # Add one day to include the end date fully
                    end_date = end_date + timedelta(days=1)
                    queryset = queryset.filter(date__lt=end_date)
                except ValueError:
                    return Response({"error": "Invalid end_date format. Use YYYY-MM-DD"}, status=400)
            
            # Apply product filter
            if product_id:
                queryset = queryset.filter(product_id=product_id)
            
            # Apply supplier filter
            if supplier_id:
                queryset = queryset.filter(
                    Q(supplier_ref_id=supplier_id) | 
                    (Q(supplier_ref__isnull=True) & Q(supplier__icontains=supplier_id))
                )
            
            # Apply client filter
            if client_id:
                queryset = queryset.filter(
                    Q(client_ref_id=client_id) | 
                    (Q(client_ref__isnull=True) & Q(client__icontains=client_id))
                )
            
            # Apply product type filter
            if product_type and product_type != 'all':
                queryset = queryset.filter(product__type=product_type)
            
            # Generate report summary
            summary = {
                'total_transactions': queryset.count(),
                'total_quantity': queryset.aggregate(total=Sum('quantity'))['total'] or 0,
                'total_value': queryset.aggregate(
                    total=Sum(F('quantity') * F('unit_price'))
                )['total'] or 0,
                'total_discount': queryset.aggregate(total=Sum('discount'))['total'] or 0,
                'total_wastage': queryset.aggregate(total=Sum('wastage'))['total'] or 0
            }
            
            # Serialize transaction data
            serializer = StockTransactionSerializer(queryset, many=True)
            
            # If export is requested, check permission and format accordingly
            if export_format:
                # Export permissions are checked in the permission class
                if export_format.lower() == 'csv':
                    # In a real implementation, this would generate a CSV file
                    # For this example, we're just adding a header to indicate it's for export
                    return Response({
                        'export_format': 'csv',
                        'summary': summary,
                        'data': serializer.data
                    })
                elif export_format.lower() == 'pdf':
                    # In a real implementation, this would generate a PDF file
                    return Response({
                        'export_format': 'pdf',
                        'summary': summary,
                        'data': serializer.data
                    })
                else:
                    return Response({"error": f"Unsupported export format: {export_format}"}, status=400)
            
            # Return regular API response
            return Response({
                'summary': summary,
                'transactions': serializer.data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)
