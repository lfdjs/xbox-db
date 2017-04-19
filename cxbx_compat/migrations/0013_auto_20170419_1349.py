# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-19 11:49
from __future__ import unicode_literals

from django.db import migrations, models
from xdb.utils.xbe import Xbe


def signature_forwards_func(apps, schema_editor):
    Executable = apps.get_model('cxbx_compat', 'Executable')
    db_alias = schema_editor.connection.alias

    all_xbe = Executable.objects.using(db_alias).all()

    for xbe in all_xbe:
        signature = bytes.fromhex(xbe.signature)
        xbe.signature_hash = Xbe.decrypt_signature(signature).hex().upper()
        xbe.save()


def signature_reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cxbx_compat', '0012_auto_20170419_1349'),
    ]

    operations = [
        migrations.RunPython(signature_forwards_func, signature_reverse_func),
    ]