# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-05 09:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0058_auto_20160728_1647'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandScorePair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cand', models.IntegerField(default=0)),
                ('score', models.FloatField(default=0.0)),
            ],
        ),
        migrations.CreateModel(
            name='MoV',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ScoreMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='VoteResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='result timestamp')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polls.Question')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.AddField(
            model_name='scoremap',
            name='result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polls.VoteResult'),
        ),
        migrations.AddField(
            model_name='mov',
            name='result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polls.VoteResult'),
        ),
        migrations.AddField(
            model_name='candscorepair',
            name='container',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polls.ScoreMap'),
        ),
    ]
