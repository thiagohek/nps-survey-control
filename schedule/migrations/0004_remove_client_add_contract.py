"""
Cleanup migration: remove ScheduledSurvey.client, make contract non-nullable,
fix related_name.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_scheduledsurvey_contract_and_more'),
        ('contracts', '0002_backfill_contracts'),
    ]

    operations = [
        # 1. Remover campo client
        migrations.RemoveField(
            model_name='scheduledsurvey',
            name='client',
        ),
        # 2. Tornar contract non-nullable e corrigir related_name
        migrations.AlterField(
            model_name='scheduledsurvey',
            name='contract',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='scheduled_survey',
                to='contracts.contract',
                verbose_name='Contrato',
            ),
        ),
    ]
