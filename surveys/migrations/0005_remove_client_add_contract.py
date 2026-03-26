"""
Cleanup migration: remove Survey.client FK, make Survey.contract non-nullable,
update unique_together.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0004_survey_contract_alter_survey_client'),
        ('contracts', '0002_backfill_contracts'),
    ]

    operations = [
        # 1. Remover unique_together antigo (client, date_conducted)
        migrations.AlterUniqueTogether(
            name='survey',
            unique_together=set(),
        ),
        # 2. Remover campo client
        migrations.RemoveField(
            model_name='survey',
            name='client',
        ),
        # 3. Tornar contract non-nullable
        migrations.AlterField(
            model_name='survey',
            name='contract',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='surveys',
                to='contracts.contract',
                verbose_name='Contrato',
            ),
        ),
        # 4. Novo unique_together (contract, date_conducted)
        migrations.AlterUniqueTogether(
            name='survey',
            unique_together={('contract', 'date_conducted')},
        ),
    ]
