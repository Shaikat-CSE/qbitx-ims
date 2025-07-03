from django.db import models

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Legacy price field for backwards compatibility
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # Track product details
    location = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    minimum_stock_level = models.IntegerField(default=5)
    unit_of_measure = models.CharField(max_length=50, default='Unit', blank=True)
    wastage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # If price is not set but buying_price and selling_price are,
        # calculate average price for backward compatibility
        if self.price is None and self.buying_price is not None and self.selling_price is not None:
            self.price = (self.buying_price + self.selling_price) / 2
        super().save(*args, **kwargs)

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Client(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class StockHistory(models.Model):
    STOCK_TYPE_CHOICES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    quantity = models.IntegerField()
    type = models.CharField(max_length=3, choices=STOCK_TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.type} - {self.quantity}"

class ProductType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    notes = models.TextField(blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    supplier_contact = models.CharField(max_length=255, blank=True, null=True)
    client = models.CharField(max_length=255, blank=True, null=True)
    client_contact = models.CharField(max_length=255, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    is_wastage = models.BooleanField(default=False)
    wastage = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    # Add relationships to Supplier and Client models
    supplier_ref = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    client_ref = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    def __str__(self):
        return f"{self.type} - {self.product.name} - {self.quantity} units"
    
    def save(self, *args, **kwargs):
        # If unit_price is not set, use the appropriate price from the product based on transaction type
        if self.unit_price is None and self.product:
            if self.type == 'IN':
                self.unit_price = self.product.buying_price
            elif self.type == 'OUT':
                self.unit_price = self.product.selling_price
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-date']
        permissions = (
            ('view_reports', 'Can view reports'),
            ('export_reports', 'Can export reports to CSV/PDF'),
            ('print_reports', 'Can print reports'),
        )
