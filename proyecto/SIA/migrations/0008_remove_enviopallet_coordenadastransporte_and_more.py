# Generated by Django 5.1 on 2024-10-06 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SIA', '0007_enviopallet_coordenadastransporte'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='enviopallet',
            name='coordenadastransporte',
        ),
        migrations.AddField(
            model_name='enviopallet',
            name='coordenadas_transporte',
            field=models.JSONField(blank=True, null=True),
        ),
    ]