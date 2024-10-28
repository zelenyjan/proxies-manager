# Generated by Django 5.1.2 on 2024-10-27 23:00

import model_utils.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('blacklisted_proxies', models.ManyToManyField(blank=True, related_name='blacklisted_clients', to='proxies.proxy')),
            ],
            options={
                'verbose_name': 'client',
                'verbose_name_plural': 'clients',
                'ordering': ['name'],
            },
        ),
    ]
