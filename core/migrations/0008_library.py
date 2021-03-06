# Generated by Django 2.2.6 on 2020-04-23 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_globalmappingtable_client'),
    ]

    operations = [
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('standard_csr_heading', models.CharField(max_length=1024)),
                ('protocol_headings', models.TextField(blank=True, null=True)),
                ('sar_headings', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'library',
            },
        ),
    ]
