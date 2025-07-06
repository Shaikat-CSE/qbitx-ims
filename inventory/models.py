from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, null=True, blank=True)  # Font Awesome icon class
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

# Add custom permissions for dashboard and reports
@receiver(post_migrate)
def create_custom_permissions(sender, **kwargs):
    if sender.name == 'inventory':
        content_type = ContentType.objects.get_for_model(User)
        
        # Create dashboard permission if it doesn't exist
        Permission.objects.get_or_create(
            codename='view_dashboard',
            name='Can view dashboard',
            content_type=content_type,
        )
        
        # Create report permission if it doesn't exist
        Permission.objects.get_or_create(
            codename='view_report',
            name='Can view reports',
            content_type=content_type,
        )

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Client(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50)  # UOM
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    shipment_number = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def profit_margin(self):
        if self.buying_price > 0:
            return ((self.selling_price - self.buying_price) / self.buying_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('wastage', 'Wastage'),
        ('return', 'Return'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    wastage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Wastage in BDT
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    transaction_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Set buying and selling price from product if not provided
        if not self.buying_price:
            self.buying_price = self.product.buying_price
        
        if not self.selling_price:
            self.selling_price = self.product.selling_price
        
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        
        # Calculate profit/loss accounting for wastage
        if self.transaction_type == 'out':
            # For sales: profit = selling price - buying price - wastage
            cost = self.quantity * self.buying_price
            revenue = self.quantity * self.unit_price
            self.profit_loss = revenue - cost - self.wastage_amount
        elif self.transaction_type == 'wastage':
            # For wastage: loss = buying price + wastage amount
            self.profit_loss = -(self.quantity * self.buying_price + self.wastage_amount)
        else:
            # For other transactions: no profit/loss calculation
            self.profit_loss = 0
        
        # Update product quantity
        if self.transaction_type == 'in' or self.transaction_type == 'return':
            self.product.quantity += self.quantity
        else:  # 'out' or 'wastage'
            self.product.quantity -= self.quantity
        
        self.product.save()
        super().save(*args, **kwargs)

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
