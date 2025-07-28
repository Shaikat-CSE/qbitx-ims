from django.db import migrations


def set_vat_rate_to_10(apps, schema_editor):
    StockTransaction = apps.get_model('inventory', 'StockTransaction')
    StockTransaction.objects.all().update(vat_rate=10)

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0015_alter_invoiceitem_quantity_alter_product_quantity_and_more'),
    ]

    operations = [
        migrations.RunPython(set_vat_rate_to_10),
    ]
