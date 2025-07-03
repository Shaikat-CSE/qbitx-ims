from rest_framework import serializers
from .models import Product, StockTransaction, ProductType, Supplier, Client

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'type', 'quantity', 'buying_price', 'selling_price', 'price',
                 'location', 'expiry_date', 'batch_number', 'barcode', 
                 'minimum_stock_level', 'unit_of_measure', 'wastage', 'created_at', 'updated_at']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'email', 'phone', 'address', 'notes', 'created_at', 'updated_at']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'contact_person', 'email', 'phone', 'address', 'notes', 'created_at', 'updated_at']

class StockTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    # Expose wastage directly from the model
    wastage = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = StockTransaction
        fields = ['id', 'product', 'product_name', 'quantity', 'type', 'notes', 
                  'supplier', 'supplier_contact', 'client', 'client_contact',
                  'reference_number', 'unit_price', 'discount', 'date', 'supplier_ref', 'client_ref',
                  'supplier_name', 'client_name', 'is_wastage', 'wastage']
    
    def get_product_name(self, obj):
        return obj.product.name
        
    def get_supplier_name(self, obj):
        if obj.supplier_ref:
            return obj.supplier_ref.name
        return obj.supplier
        
    def get_client_name(self, obj):
        if obj.client_ref:
            return obj.client_ref.name
        return obj.client
    
class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name']