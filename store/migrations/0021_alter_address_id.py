# Generated by Django 3.2.3 on 2023-12-28 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_productimage_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='Address Id'),
        ),
    ]
