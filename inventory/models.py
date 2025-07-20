from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, null=True, blank=True)  # Font Awesome icon class
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

# Add Warehouse model
class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

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
    sku = models.CharField(max_length=50)  # Removed unique=True
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50)  # UOM
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=3, default=10)
    shipment_number = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    expiry_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Same SKU can exist in different warehouses
        unique_together = [['sku', 'warehouse']]
    
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
        ('transfer', 'Warehouse Transfer'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('due', 'Due'),
        ('partial', 'Partially Paid'),
        ('credit', 'Credit'),
        ('na', 'Not Applicable'),
    )
    
    transaction_id = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Unique transaction identifier")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    wastage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Additional wastage cost beyond the item value (e.g., disposal fees)")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_transactions')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_transactions')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    transaction_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Tax fields
    apply_taxes = models.BooleanField(default=False)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ait_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Payment fields
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='na')
    payment_due_date = models.DateField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        if self.transaction_id:
            return f"{self.transaction_id} - {self.transaction_type} - {self.product.name}"
        return f"{self.transaction_type} - {self.product.name} - {self.quantity}"
    
    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        prefix = {
            'in': 'IN',
            'out': 'OUT',
            'wastage': 'WST',
            'return': 'RTN',
            'transfer': 'TRF'
        }.get(self.transaction_type, 'TXN')
        
        # Get current date in YYMMDD format
        date_str = self.transaction_date.strftime('%y%m%d')
        
        # Get count of transactions for today with same type
        today_start = self.transaction_date.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = self.transaction_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        count = StockTransaction.objects.filter(
            transaction_type=self.transaction_type,
            transaction_date__gte=today_start,
            transaction_date__lte=today_end
        ).count() + 1
        
        # Format: PREFIX-YYMMDD-NNNN (e.g., IN-230415-0001)
        return f"{prefix}-{date_str}-{count:04d}"
    
    def calculate_final_price(self):
        """Calculate the final price after tax deductions"""
        if not self.apply_taxes:
            return self.selling_price
        
        # Apply VAT deduction first
        price_after_vat = self.selling_price * (1 - (self.vat_rate / 100))
        
        # Then apply AIT deduction
        final_price = price_after_vat * (1 - (self.ait_rate / 100))
        
        return final_price
    
    @property
    def payment_percentage(self):
        """Calculate the percentage of payment made"""
        if self.total_price == 0:
            return 100
        return (self.amount_paid / self.total_price) * 100
    
    def save(self, *args, **kwargs):
        # Generate transaction_id if not provided
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        # Set buying and selling price from product if not provided
        if not self.buying_price:
            self.buying_price = self.product.buying_price
        
        if not self.selling_price:
            self.selling_price = self.product.selling_price
        
        # Set default values for wastage transactions
        if self.transaction_type == 'wastage':
            # For wastage, no taxes apply
            self.apply_taxes = False
            self.vat_rate = 0
            self.ait_rate = 0
            self.final_price = 0
            # Unit price is the buying price for wastage
            self.unit_price = self.buying_price
        
        # Calculate total price
        if self.transaction_type == 'out' and self.apply_taxes:
            # For outgoing transactions with taxes, ensure final_price is set
            if self.final_price is None or self.final_price == 0:
                self.final_price = self.calculate_final_price()
            self.total_price = self.quantity * self.final_price
            self.unit_price = self.final_price
        else:
            self.total_price = self.quantity * self.unit_price
        
        # Calculate profit/loss accounting for wastage and taxes
        if self.transaction_type == 'out':
            # For sales: profit = selling price - buying price - wastage
            cost = self.quantity * self.buying_price
            
            # If taxes are applied, use final_price for revenue calculation
            if self.apply_taxes and self.final_price:
                # Final price already reflects the tax deductions, so use it directly
                revenue = self.quantity * self.final_price
                # Update total_price to reflect the final price after tax
                self.total_price = revenue
            else:
                revenue = self.quantity * self.selling_price
                
            self.profit_loss = revenue - cost - self.wastage_amount
        elif self.transaction_type == 'wastage':
            # For wastage: loss = total price (which is already calculated as quantity * unit price)
            # This avoids double counting and ensures profit_loss matches the total price for wastage
            self.profit_loss = -self.total_price
        else:
            # For other transactions: no profit/loss calculation
            self.profit_loss = 0
        
        # Set amount_due based on payment_status
        if self.payment_status == 'paid':
            self.amount_paid = self.total_price
            self.amount_due = 0
        elif self.payment_status == 'due':
            self.amount_paid = 0
            self.amount_due = self.total_price
        elif self.payment_status == 'partial':
            # For partial payments, keep the amount_paid as is and calculate amount_due
            if self.amount_paid > self.total_price:
                self.amount_paid = self.total_price
            self.amount_due = self.total_price - self.amount_paid
        elif self.payment_status == 'na':
            # For non-applicable payment status (e.g., wastage)
            self.amount_paid = 0
            self.amount_due = 0
        
        # Flag to check if this is a new transaction
        is_new = self.pk is None
        
        # Store current product state before saving
        old_product = None
        if not is_new:
            try:
                old_product = StockTransaction.objects.get(pk=self.pk)
            except StockTransaction.DoesNotExist:
                pass
        
        # Save the transaction first without updating product quantities
        super().save(*args, **kwargs)
        
        # Now update product quantity and warehouse based on transaction type
        if is_new:  # Only update quantities for new transactions
            if self.transaction_type == 'in' or self.transaction_type == 'return':
                # For incoming transactions, increase product quantity
                self.product.quantity += self.quantity
                # Update warehouse if specified
                if self.destination_warehouse:
                    self.product.warehouse = self.destination_warehouse
                self.product.save()
            elif self.transaction_type == 'out' or self.transaction_type == 'wastage':
                # For outgoing transactions, ensure source_warehouse is set to product's warehouse if not specified
                if not self.source_warehouse and self.product.warehouse:
                    self.source_warehouse = self.product.warehouse
                    # Need to save again to update the source_warehouse
                    super().save(update_fields=['source_warehouse'])
                
                # Decrease product quantity
                self.product.quantity -= self.quantity
                self.product.save()
            elif self.transaction_type == 'transfer':
                # For warehouse transfers, handle quantity and warehouse updates correctly
                try:
                    # 1. First check if source and destination warehouses are specified
                    if not self.source_warehouse:
                        raise ValidationError("Source warehouse must be specified for transfers")
                    
                    if not self.destination_warehouse:
                        raise ValidationError("Destination warehouse must be specified for transfers")
                    
                    # 2. Check if source and destination are different
                    if self.source_warehouse == self.destination_warehouse:
                        raise ValidationError("Source and destination warehouses cannot be the same")
                    
                    # 3. Check if the product is in the source warehouse
                    if self.product.warehouse != self.source_warehouse:
                        raise ValidationError(f"Product is not in the source warehouse. Current warehouse: {self.product.warehouse}")
                    
                    # 4. Check if there's enough quantity in the source warehouse
                    if self.product.quantity < self.quantity:
                        raise ValidationError(f"Not enough quantity in source warehouse. Available: {self.product.quantity}, Requested: {self.quantity}")
                    
                    # 5. Check if quantity is positive
                    if self.quantity <= 0:
                        raise ValidationError("Transfer quantity must be greater than zero")
                    
                    # 6. Reduce quantity from source warehouse
                    self.product.quantity -= self.quantity
                    if self.product.quantity < 0:
                        raise ValidationError("Transfer would result in negative inventory in source warehouse")
                    
                    self.product.save()
                    
                    # 7. Check if product with same SKU exists in destination warehouse
                    try:
                        destination_product = Product.objects.filter(
                            sku=self.product.sku,
                            warehouse=self.destination_warehouse
                        ).first()
                        
                        if destination_product:
                            # If product exists in destination warehouse, increase its quantity
                            destination_product.quantity += self.quantity
                            destination_product.save()
                        else:
                            # Create a new product entry for the destination warehouse
                            try:
                                new_product = Product.objects.create(
                                    name=self.product.name,
                                    sku=self.product.sku,
                                    category=self.product.category,
                                    description=self.product.description,
                                    buying_price=self.product.buying_price,
                                    selling_price=self.product.selling_price,
                                    unit_of_measure=self.product.unit_of_measure,
                                    quantity=self.quantity,
                                    reorder_level=self.product.reorder_level,
                                    shipment_number=self.product.shipment_number,
                                    location=self.product.location,
                                    warehouse=self.destination_warehouse,
                                    expiry_date=self.product.expiry_date,
                                    supplier=self.product.supplier
                                )
                            except Exception as e:
                                # Rollback the quantity reduction in source warehouse if destination creation fails
                                self.product.quantity += self.quantity
                                self.product.save()
                                raise ValidationError(f"Failed to create product in destination warehouse: {str(e)}")
                    except Exception as e:
                        # Rollback the quantity reduction in source warehouse if any error occurs
                        self.product.quantity += self.quantity
                        self.product.save()
                        raise ValidationError(f"Error during warehouse transfer: {str(e)}")
                
                except ValidationError as e:
                    # Re-raise ValidationError with the specific error message
                    raise ValidationError(f"Warehouse transfer failed: {str(e)}")
                except Exception as e:
                    # Catch any other exceptions and provide a meaningful error message
                    raise ValidationError(f"Unexpected error during warehouse transfer: {str(e)}")
        
        # Auto-generate invoice for new outgoing transactions with clients
        if is_new and self.transaction_type == 'out' and self.client:
            self.generate_invoice()
    
    def generate_invoice(self):
        """Generate an invoice for this transaction"""
        # Check if an invoice already exists for this transaction
        reference_number = f"TRANS-{self.id}"
        
        # Import here to avoid circular import
        from django.db.models import Max
        
        # Get the Invoice model without importing it directly
        Invoice = type(self)._meta.model._meta.apps.get_model('inventory', 'Invoice')
        InvoiceItem = type(self)._meta.model._meta.apps.get_model('inventory', 'InvoiceItem')
        
        existing_invoice = Invoice.objects.filter(notes__contains=reference_number).first()
        
        if not existing_invoice:
            # Generate next invoice number
            last_invoice = Invoice.objects.aggregate(Max('invoice_number'))['invoice_number__max']
            next_number = 1
            if last_invoice:
                try:
                    next_number = int(last_invoice) + 1
                except ValueError:
                    next_number = 1
            
            # Create the invoice
            invoice = Invoice.objects.create(
                invoice_number=f'{next_number:06d}',
                client=self.client,
                issue_date=self.transaction_date.date(),
                due_date=self.transaction_date.date() + timezone.timedelta(days=30),
                status='pending' if self.payment_status in ['due', 'partial', 'credit'] else 'paid',
                subtotal=self.total_price,
                tax_rate=self.vat_rate + self.ait_rate if self.apply_taxes else 0,
                tax_amount=self.total_price - (self.quantity * self.final_price) if self.apply_taxes and self.final_price else 0,
                discount=0,
                total=self.total_price,
                notes=f"{reference_number} - Auto-generated from transaction #{self.id} on {timezone.now().strftime('%Y-%m-%d')}",
                created_by=self.created_by
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                product=self.product,
                quantity=self.quantity,
                unit_price=self.unit_price,
                total_price=self.total_price
            )
            
            return invoice
        
        return existing_invoice


class Payment(models.Model):
    """Model to track individual payments for stock transactions"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Banking'),
        ('other', 'Other'),
    )
    
    transaction = models.ForeignKey(StockTransaction, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cash')
    reference = models.CharField(max_length=100, blank=True, null=True)  # Reference number, check number, etc.
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment of {self.amount} for {self.transaction}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update the related transaction's payment status
        transaction = self.transaction
        total_payments = Payment.objects.filter(transaction=transaction).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Update transaction payment details
        transaction.amount_paid = total_payments
        
        # Determine payment status based on the amount paid
        if total_payments >= transaction.total_price:
            transaction.payment_status = 'paid'
            transaction.amount_paid = transaction.total_price  # Cap at total price
            transaction.amount_due = 0
        elif total_payments > 0:
            transaction.payment_status = 'partial'
            transaction.amount_due = transaction.total_price - total_payments
        else:
            transaction.payment_status = 'due'
            transaction.amount_due = transaction.total_price
        
        # Save the transaction without triggering its save method recursively
        StockTransaction.objects.filter(id=transaction.id).update(
            payment_status=transaction.payment_status,
            amount_paid=transaction.amount_paid,
            amount_due=transaction.amount_due
        )

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
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
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
