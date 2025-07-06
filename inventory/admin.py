from django.contrib import admin
from .models import Category, Supplier, Client, Product, StockTransaction, Invoice, InvoiceItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'city', 'country')
    list_filter = ('country', 'city')
    search_fields = ('name', 'contact_person', 'email', 'phone')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'city', 'country')
    list_filter = ('country', 'city')
    search_fields = ('name', 'contact_person', 'email', 'phone')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'quantity', 'unit_of_measure', 'buying_price', 'selling_price', 'profit_margin', 'is_low_stock')
    list_filter = ('category', 'supplier')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('profit_margin', 'is_low_stock')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'issue_date', 'due_date', 'status', 'total')
    list_filter = ('status', 'issue_date')
    search_fields = ('invoice_number', 'client__name')
    inlines = [InvoiceItemInline]

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'unit_price', 'total_price', 'transaction_date', 'created_by')
    list_filter = ('transaction_type', 'transaction_date', 'created_by')
    search_fields = ('product__name', 'reference_number', 'notes')
    date_hierarchy = 'transaction_date'
