from django import forms
from .models import Product, Category, Supplier, Client, StockTransaction, Invoice, InvoiceItem, Warehouse, Payment
from django.utils import timezone

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'description', 'buying_price', 'selling_price', 
                  'unit_of_measure', 'quantity', 'reorder_level', 'shipment_number', 
                  'warehouse', 'expiry_date', 'supplier']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'shipment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        sku = cleaned_data.get('sku')
        warehouse = cleaned_data.get('warehouse')
        
        # Check if a product with the same SKU exists in the same warehouse
        if sku and warehouse:
            # Exclude current instance when editing
            instance_id = self.instance.id if self.instance and self.instance.pk else None
            
            existing_product = Product.objects.filter(sku=sku, warehouse=warehouse).exclude(id=instance_id).first()
            if existing_product:
                self.add_error('sku', f'A product with SKU "{sku}" already exists in the selected warehouse.')
        
        return cleaned_data

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-box'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'city', 'country', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'city', 'country', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'transaction_type', 'quantity', 'buying_price', 
                  'selling_price', 'wastage_amount', 'supplier', 'client', 
                  'source_warehouse', 'destination_warehouse', 'reference_number', 
                  'notes', 'transaction_date', 'apply_taxes', 'vat_rate', 'ait_rate', 'final_price',
                  'payment_status', 'payment_due_date', 'amount_paid']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'updateFormFields()'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'wastage_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'source_warehouse': forms.Select(attrs={'class': 'form-select warehouse-field'}),
            'destination_warehouse': forms.Select(attrs={'class': 'form-select warehouse-field'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'transaction_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'apply_taxes': forms.HiddenInput(),
            'vat_rate': forms.HiddenInput(),
            'ait_rate': forms.HiddenInput(),
            'final_price': forms.HiddenInput(),
            'payment_status': forms.Select(attrs={'class': 'form-select', 'onchange': 'updatePaymentFields()'}),
            'payment_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['buying_price'].required = False
        self.fields['selling_price'].required = False
        self.fields['source_warehouse'].required = False
        self.fields['destination_warehouse'].required = False
        self.fields['apply_taxes'].required = False
        self.fields['vat_rate'].required = False
        self.fields['ait_rate'].required = False
        self.fields['final_price'].required = False
        self.fields['payment_due_date'].required = False
        self.fields['amount_paid'].required = False
        
        if 'instance' in kwargs and kwargs['instance'] is not None:
            # If editing existing instance, set initial values
            instance = kwargs['instance']
            self.fields['buying_price'].initial = instance.buying_price
            self.fields['selling_price'].initial = instance.selling_price
        
        # Add product change event listener to update prices
        self.fields['product'].widget.attrs.update({'onchange': 'updateProductPrices()'})
        
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        transaction_type = cleaned_data.get('transaction_type')
        payment_status = cleaned_data.get('payment_status')
        
        # If product is selected but prices aren't provided, use product's prices
        if product:
            if not cleaned_data.get('buying_price'):
                cleaned_data['buying_price'] = product.buying_price
                
            if not cleaned_data.get('selling_price'):
                cleaned_data['selling_price'] = product.selling_price
                
            # Set unit_price based on transaction type
            if transaction_type == 'out':
                # If taxes are applied, use final price as unit price
                if cleaned_data.get('apply_taxes') and cleaned_data.get('final_price'):
                    cleaned_data['unit_price'] = cleaned_data.get('final_price')
                else:
                    cleaned_data['unit_price'] = cleaned_data.get('selling_price')
            else:
                cleaned_data['unit_price'] = cleaned_data.get('buying_price')
        
        # Validate warehouse fields based on transaction type
        if transaction_type == 'transfer':
            source = cleaned_data.get('source_warehouse')
            destination = cleaned_data.get('destination_warehouse')
            quantity = cleaned_data.get('quantity', 0)
            
            if not source:
                self.add_error('source_warehouse', 'Source warehouse is required for transfers')
                
            if not destination:
                self.add_error('destination_warehouse', 'Destination warehouse is required for transfers')
                
            if source and destination and source == destination:
                self.add_error('destination_warehouse', 'Source and destination warehouses cannot be the same')
            
            # Validate quantity is positive
            if quantity <= 0:
                self.add_error('quantity', 'Transfer quantity must be greater than zero')
                
            # Check if product is in source warehouse
            if product and source and product.warehouse != source:
                self.add_error('source_warehouse', f'Product is not in the source warehouse. Current warehouse: {product.warehouse}')
                
            # Check if there's enough quantity
            if product and quantity > product.quantity:
                self.add_error('quantity', f'Not enough quantity in source warehouse. Available: {product.quantity}, Requested: {quantity}')
        
        # For stock in, destination warehouse is required
        if transaction_type == 'in' and not cleaned_data.get('destination_warehouse'):
            self.add_error('destination_warehouse', 'Destination warehouse is required for stock in')
            
        # For stock out, source warehouse should be set if available
        if transaction_type == 'out' and product and product.warehouse:
            if not cleaned_data.get('source_warehouse'):
                cleaned_data['source_warehouse'] = product.warehouse
        
        # Payment validation
        if payment_status in ['due', 'partial', 'credit'] and not cleaned_data.get('payment_due_date'):
            self.add_error('payment_due_date', 'Due date is required for non-paid transactions')
            
        if payment_status == 'partial':
            amount_paid = cleaned_data.get('amount_paid') or 0
            
            # Calculate total price to validate partial payment
            quantity = cleaned_data.get('quantity') or 0
            unit_price = cleaned_data.get('unit_price') or 0
            if cleaned_data.get('apply_taxes') and cleaned_data.get('final_price'):
                unit_price = cleaned_data.get('final_price')
            
            total_price = quantity * unit_price
            
            if amount_paid <= 0:
                self.add_error('amount_paid', 'Partial payment amount must be greater than zero')
            elif amount_paid >= total_price:
                self.add_error('amount_paid', 'Partial payment cannot be equal to or greater than the total amount')
        
        # Ensure transaction_date is timezone-aware
        transaction_date = cleaned_data.get('transaction_date')
        if transaction_date and timezone.is_naive(transaction_date):
            cleaned_data['transaction_date'] = timezone.make_aware(transaction_date)
        
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['transaction', 'amount', 'payment_date', 'payment_method', 'reference', 'notes']
        widgets = {
            'transaction': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        # Allow filtering transactions by client, supplier, or transaction type
        transaction_filters = kwargs.pop('transaction_filters', {})
        super().__init__(*args, **kwargs)
        
        # Apply filters to the transaction queryset if provided
        if transaction_filters:
            self.fields['transaction'].queryset = StockTransaction.objects.filter(
                **transaction_filters
            ).exclude(payment_status='paid').order_by('-transaction_date')
        else:
            # By default, only show unpaid transactions
            self.fields['transaction'].queryset = StockTransaction.objects.exclude(
                payment_status='paid'
            ).exclude(payment_status='na').order_by('-transaction_date')
    
    def clean(self):
        cleaned_data = super().clean()
        transaction = cleaned_data.get('transaction')
        amount = cleaned_data.get('amount')
        
        if transaction and amount:
            # Check if amount is valid for this transaction
            amount_due = transaction.amount_due
            
            if amount <= 0:
                self.add_error('amount', 'Payment amount must be greater than zero')
            elif amount > amount_due:
                self.add_error('amount', f'Payment amount cannot exceed the due amount ({amount_due})')
        
        return cleaned_data

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'client', 'issue_date', 'due_date', 'status', 
                  'subtotal', 'tax_rate', 'discount', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'subtotal': forms.HiddenInput(),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make calculated fields not required in the form
        self.fields['subtotal'].required = False

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True
) 