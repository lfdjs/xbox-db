# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-29 11:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cxbx_compat', '0005_remove_build_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Executable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=256)),
                ('signature', models.CharField(max_length=512, unique=True)),
                ('disk_path', models.CharField(max_length=1024)),
                ('title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cxbx_compat.Title')),
            ],
        ),
    ]
