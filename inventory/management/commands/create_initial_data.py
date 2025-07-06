from django.core.management.base import BaseCommand
from inventory.models import Category, Supplier, Client
from django.utils import timezone

class Command(BaseCommand):
    help = 'Creates initial data for the inventory system'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')
        
        # Create categories
        categories = [
            {'name': 'Fruits', 'icon': 'fa-apple-alt'},
            {'name': 'Spice', 'icon': 'fa-pepper-hot'},
            {'name': 'Home Decor', 'icon': 'fa-home'},
            {'name': 'Cookware', 'icon': 'fa-utensils'},
            {'name': 'Bakery Ingredients', 'icon': 'fa-bread-slice'},
        ]
        
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'icon': category_data['icon']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Create suppliers
        suppliers = [
            {
                'name': 'Global Foods Inc.',
                'contact_person': 'John Smith',
                'email': 'john@globalfoods.com',
                'phone': '555-123-4567',
                'address': '123 Main St',
                'city': 'New York',
                'country': 'USA',
            },
            {
                'name': 'Asian Spice Traders',
                'contact_person': 'Li Wei',
                'email': 'li@asianspice.com',
                'phone': '555-987-6543',
                'address': '456 Spice Road',
                'city': 'Singapore',
                'country': 'Singapore',
            },
            {
                'name': 'European Home Goods',
                'contact_person': 'Marie Dupont',
                'email': 'marie@eurohome.com',
                'phone': '555-456-7890',
                'address': '789 Avenue de Paris',
                'city': 'Paris',
                'country': 'France',
            },
        ]
        
        for supplier_data in suppliers:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults={
                    'contact_person': supplier_data['contact_person'],
                    'email': supplier_data['email'],
                    'phone': supplier_data['phone'],
                    'address': supplier_data['address'],
                    'city': supplier_data['city'],
                    'country': supplier_data['country'],
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')
            else:
                self.stdout.write(f'Supplier already exists: {supplier.name}')
        
        # Create clients
        clients = [
            {
                'name': 'Local Grocery Store',
                'contact_person': 'Sarah Johnson',
                'email': 'sarah@localgrocery.com',
                'phone': '555-222-3333',
                'address': '101 Market St',
                'city': 'Chicago',
                'country': 'USA',
            },
            {
                'name': 'Gourmet Restaurant',
                'contact_person': 'Chef Antonio',
                'email': 'antonio@gourmet.com',
                'phone': '555-444-5555',
                'address': '202 Culinary Blvd',
                'city': 'Los Angeles',
                'country': 'USA',
            },
            {
                'name': 'Home Decor Boutique',
                'contact_person': 'Emma Wilson',
                'email': 'emma@decorshop.com',
                'phone': '555-666-7777',
                'address': '303 Design Ave',
                'city': 'Miami',
                'country': 'USA',
            },
        ]
        
        for client_data in clients:
            client, created = Client.objects.get_or_create(
                name=client_data['name'],
                defaults={
                    'contact_person': client_data['contact_person'],
                    'email': client_data['email'],
                    'phone': client_data['phone'],
                    'address': client_data['address'],
                    'city': client_data['city'],
                    'country': client_data['country'],
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )
            if created:
                self.stdout.write(f'Created client: {client.name}')
            else:
                self.stdout.write(f'Client already exists: {client.name}')
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!')) 