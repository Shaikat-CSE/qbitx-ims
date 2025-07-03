from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Product, StockHistory, ProductType, Supplier, Client, StockTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'type', 'quantity', 'price')
    list_filter = ('type',)
    search_fields = ('name', 'sku')

@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'type', 'date', 'notes')
    list_filter = ('type', 'date')
    search_fields = ('product__name', 'notes')

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'contact_person', 'email')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'contact_person', 'email')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'type', 'date', 'supplier', 'client', 'reference_number')
    list_filter = ('type', 'date', 'is_wastage')
    search_fields = ('product__name', 'supplier', 'client', 'reference_number')
    raw_id_fields = ('product', 'supplier_ref', 'client_ref')
    fieldsets = (
        (None, {
            'fields': ('product', 'quantity', 'type', 'date', 'notes')
        }),
        ('Financial Information', {
            'fields': ('unit_price', 'discount', 'is_wastage', 'wastage'),
            'classes': ('collapse',)
        }),
        ('References', {
            'fields': ('reference_number', 'supplier', 'supplier_contact', 'client', 'client_contact', 'supplier_ref', 'client_ref'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Add a note to highlight the new report permissions
        if not hasattr(self, '_permissions_note_shown') and request.user.is_superuser:
            self._permissions_note_shown = True
            self.message_user(request, (
                "New report permissions are available for users: "
                "'Can view reports', 'Can export reports to CSV/PDF', and 'Can print reports'. "
                "Assign these permissions to users who need to access the reports section."
            ))
        return super().get_queryset(request)

# Register Report Permissions explicitly to make them visible in admin
class ReportPermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # Filter to only show report-related permissions
        content_type = ContentType.objects.get_for_model(StockTransaction)
        return Permission.objects.filter(
            content_type=content_type,
            codename__in=['view_reports', 'export_reports', 'print_reports']
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    list_display = ('name', 'codename', 'content_type')

# Register the model if it doesn't interfere with Django's built-in permission admin
# This is optional and would need to be tested in the actual application
# admin.site.register(Permission, ReportPermissionAdmin)
