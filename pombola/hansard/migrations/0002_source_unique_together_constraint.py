# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hansard', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('name', 'list_page')]),
        ),
    ]
