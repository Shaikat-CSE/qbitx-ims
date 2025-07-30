from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Sum, F, IntegerField
from django.db.models.functions import Coalesce
from inventory.models import Product, StockTransaction
from datetime import date

class Command(BaseCommand):
    help = 'Calculate and cache overall inventory totals for the inventory report.'

    def handle(self, *args, **options):
        today = date.today()
        products = Product.objects.all()
        
        overall_total_opening_stock = 0
        overall_total_purchase_stock = 0
        overall_total_sale_stock = 0
        overall_total_wastage_stock = 0
        overall_total_stock = 0
        overall_total_closing_stock = 0

        for product in products:
            # Calculate opening stock
            opening_purchases = StockTransaction.objects.filter(
                product=product,
                transaction_type='in',
                transaction_date__date__lt=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            opening_sales = StockTransaction.objects.filter(
                product=product,
                transaction_type='out',
                transaction_date__date__lt=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            opening_wastage = StockTransaction.objects.filter(
                product=product,
                transaction_type='wastage',
                transaction_date__date__lt=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            purchases_since_start = StockTransaction.objects.filter(
                product=product,
                transaction_type='in',
                transaction_date__date__gte=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            sales_since_start = StockTransaction.objects.filter(
                product=product,
                transaction_type='out',
                transaction_date__date__gte=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            wastage_since_start = StockTransaction.objects.filter(
                product=product,
                transaction_type='wastage',
                transaction_date__date__gte=today
            ).aggregate(total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField()))['total_quantity']

            current_product_quantity = product.quantity
            calculated_opening_stock = current_product_quantity - purchases_since_start + sales_since_start + wastage_since_start
            if calculated_opening_stock < 0:
                calculated_opening_stock = 0

            purchase_stock_in_period = purchases_since_start
            sale_stock_in_period = sales_since_start
            wastage_stock_in_period = wastage_since_start

            total_stock = calculated_opening_stock + purchase_stock_in_period
            closing_stock = total_stock - sale_stock_in_period - wastage_stock_in_period
            if closing_stock < 0:
                closing_stock = 0

            overall_total_opening_stock += calculated_opening_stock
            overall_total_purchase_stock += purchase_stock_in_period
            overall_total_sale_stock += sale_stock_in_period
            overall_total_wastage_stock += wastage_stock_in_period
            overall_total_stock += total_stock
            overall_total_closing_stock += closing_stock

        cache.set('overall_inventory_totals', {
            'overall_total_opening_stock': overall_total_opening_stock,
            'overall_total_purchase_stock': overall_total_purchase_stock,
            'overall_total_sale_stock': overall_total_sale_stock,
            'overall_total_wastage_stock': overall_total_wastage_stock,
            'overall_total_stock': overall_total_stock,
            'overall_total_closing_stock': overall_total_closing_stock,
        }, timeout=60*60*2)  # 2 hours

        self.stdout.write(self.style.SUCCESS('Overall inventory totals cached successfully.'))
