# Generated by Django 2.2.6 on 2020-04-17 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_clientinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientinfo',
            name='client_name',
            field=models.CharField(error_messages={'unique': 'Client is already existed.'}, max_length=32, unique=True),
        ),
    ]
