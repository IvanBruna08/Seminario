# Generated by Django 5.1 on 2024-10-09 21:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SIA', '0010_recepcion_peso_ingresado_alter_pallet_estado_envio_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pallet',
            name='distribuidor',
        ),
    ]