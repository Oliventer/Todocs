# Generated by Django 3.1 on 2020-12-20 17:20

import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0004_auto_20201220_1918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location='/files/'), upload_to=''),
        ),
    ]
