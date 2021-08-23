# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-23 19:10
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipam', '0013_prefix_add_is_pool'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, b'Active'), (2, b'Reserved'), (3, b'Deprecated'), (5, b'DHCP')], default=1, verbose_name=b'Status'),
        ),
    ]