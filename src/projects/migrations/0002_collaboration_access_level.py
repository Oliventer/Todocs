# Generated by Django 3.1 on 2020-12-25 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='collaboration',
            name='access_level',
            field=models.TextField(choices=[('readonly', 'Read Only'), ('edit', 'Edit'), ('owner', 'Owner')], default='readonly'),
            preserve_default=False,
        ),
    ]
