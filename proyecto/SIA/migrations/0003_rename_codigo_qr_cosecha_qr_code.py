# Generated by Django 5.1 on 2024-09-05 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SIA', '0002_cosecha'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cosecha',
            old_name='codigo_qr',
            new_name='qr_code',
        ),
    ]
