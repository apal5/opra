# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-29 02:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0024_question_send_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='poll_algorithm',
            field=models.IntegerField(default=1),
        ),
    ]