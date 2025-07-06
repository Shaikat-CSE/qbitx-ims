from django import forms
from .models import Product, Category, Supplier, Client, StockTransaction, Invoice, InvoiceItem
from django.utils import timezone

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'description', 'buying_price', 'selling_price', 
                  'unit_of_measure', 'quantity', 'reorder_level', 'shipment_number', 
                  'location', 'expiry_date', 'supplier']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'shipment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
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
                  'selling_price', 'wastage_amount', 'supplier', 'client', 'reference_number', 
                  'notes', 'transaction_date']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'wastage_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'transaction_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['buying_price'].required = False
        self.fields['selling_price'].required = False
        
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
        
        # If product is selected but prices aren't provided, use product's prices
        if product:
            if not cleaned_data.get('buying_price'):
                cleaned_data['buying_price'] = product.buying_price
                
            if not cleaned_data.get('selling_price'):
                cleaned_data['selling_price'] = product.selling_price
                
            # Set unit_price based on transaction type
            if transaction_type == 'out':
                cleaned_data['unit_price'] = cleaned_data.get('selling_price')
            else:
                cleaned_data['unit_price'] = cleaned_data.get('buying_price')
        
        # Ensure transaction_date is timezone-aware
        transaction_date = cleaned_data.get('transaction_date')
        if transaction_date and timezone.is_naive(transaction_date):
            cleaned_data['transaction_date'] = timezone.make_aware(transaction_date)
        
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
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True
) 