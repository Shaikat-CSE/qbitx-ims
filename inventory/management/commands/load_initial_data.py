import json
from django.core.management.base import BaseCommand
from inventory.models import Product, ProductType, StockHistory

class Command(BaseCommand):
    help = 'Load initial data for the inventory system'

    def handle(self, *args, **kwargs):
        # Sample product data from frontend app.js
        sample_products = [
            { "id": 1, "name": "Gold Necklace", "sku": "GN-001", "type": "Jewelry", "quantity": 25, "price": 599.99 },
            { "id": 2, "name": "Silver Bracelet", "sku": "SB-002", "type": "Jewelry", "quantity": 40, "price": 199.99 },
            { "id": 3, "name": "Diamond Ring", "sku": "DR-003", "type": "Jewelry", "quantity": 10, "price": 1299.99 },
            { "id": 4, "name": "Pearl Earrings", "sku": "PE-004", "type": "Jewelry", "quantity": 30, "price": 249.99 },
            { "id": 5, "name": "Wrist Watch", "sku": "WW-005", "type": "Accessories", "quantity": 15, "price": 499.99 },
            { "id": 6, "name": "Leather Belt", "sku": "LB-006", "type": "Accessories", "quantity": 50, "price": 79.99 },
            { "id": 7, "name": "Sunglasses", "sku": "SG-007", "type": "Accessories", "quantity": 45, "price": 129.99 },
            { "id": 8, "name": "Wallet", "sku": "WL-008", "type": "Accessories", "quantity": 35, "price": 89.99 },
            { "id": 9, "name": "Scarf", "sku": "SC-009", "type": "Apparel", "quantity": 55, "price": 39.99 },
            { "id": 10, "name": "Dress Shirt", "sku": "DS-010", "type": "Apparel", "quantity": 3, "price": 69.99 }
        ]

        # Sample stock history from frontend app.js
        sample_stock_history = [
            { "id": 1, "productId": 1, "productName": "Gold Necklace", "quantity": 10, "type": "IN", "notes": "Initial stock", "date": "2025-04-15T00:00:00.000Z" },
            { "id": 2, "productId": 3, "productName": "Diamond Ring", "quantity": 5, "type": "IN", "notes": "New shipment", "date": "2025-04-17T00:00:00.000Z" },
            { "id": 3, "productId": 5, "productName": "Wrist Watch", "quantity": 8, "type": "IN", "notes": "Restocking", "date": "2025-04-22T00:00:00.000Z" },
            { "id": 4, "productId": 2, "productName": "Silver Bracelet", "quantity": 3, "type": "OUT", "notes": "Store display", "date": "2025-04-23T00:00:00.000Z" },
            { "id": 5, "productId": 10, "productName": "Dress Shirt", "quantity": 2, "type": "OUT", "notes": "Customer order #1289", "date": "2025-04-25T00:00:00.000Z" }
        ]

        # Sample product types from frontend app.js
        product_types = ['Jewelry', 'Accessories', 'Apparel', 'Home Decor', 'Gifts']

        # Create product types
        for type_name in product_types:
            ProductType.objects.get_or_create(name=type_name)
            self.stdout.write(self.style.SUCCESS(f'Created product type: {type_name}'))

        # Create products
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults={
                    'name': product_data['name'],
                    'type': product_data['type'],
                    'quantity': product_data['quantity'],
                    'price': product_data['price']
                }
            )
            
            status = 'Created' if created else 'Already exists'
            self.stdout.write(self.style.SUCCESS(f'{status}: {product.name}'))

        # Import stock history if needed
        # Note: We skip this for now as products already have quantities
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded initial data')) 