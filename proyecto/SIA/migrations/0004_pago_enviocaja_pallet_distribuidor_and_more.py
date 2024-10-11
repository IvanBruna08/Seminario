# Generated by Django 5.1 on 2024-10-03 17:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SIA', '0003_caja_fecha_caja'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='enviocaja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIA.enviocaja'),
        ),
        migrations.AddField(
            model_name='pallet',
            name='distribuidor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='SIA.distribuidor'),
        ),
        migrations.AddField(
            model_name='pallet',
            name='estado_envio',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('completado', 'Completado'), ('en_proceso', 'En Proceso')], default='pendiente', max_length=50),
        ),
    ]
