# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-23 00:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0021_auto_20160622_1211'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='members',
        ),
        migrations.RemoveField(
            model_name='group',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Group',
        ),
    ]
