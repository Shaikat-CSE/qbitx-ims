from django.core.management.base import BaseCommand
from inventory.models import Product

class Command(BaseCommand):
    help = 'Clears all products from the database'

    def handle(self, *args, **kwargs):
        # Delete all existing products
        count = Product.objects.count()
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} products')) 