from django.core.management.base import BaseCommand
from inventory.models import ProductType

class Command(BaseCommand):
    help = 'Sets up the required product types'

    def handle(self, *args, **kwargs):
        # Delete all existing product types
        ProductType.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing product types'))
        
        # Create new product types
        product_types = [
            'Fruits',
            'Spice',
            'Home Decor',
            'Cookware',
            'Bakery Ingredients'
        ]
        
        for type_name in product_types:
            ProductType.objects.create(name=type_name)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(product_types)} product types')) 