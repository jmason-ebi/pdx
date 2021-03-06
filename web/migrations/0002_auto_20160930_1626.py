# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-30 16:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='gene',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='tumor',
            name='diagnosis',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='tumor',
            name='tissue_of_origin',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='tumor',
            name='tumor_type',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
