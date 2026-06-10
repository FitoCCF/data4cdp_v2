# Generated manually to remove obsolete fields from CorrectiveTask

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0007_migrate_corrective_tasks'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='correctivetask',
            name='year',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='week',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='day',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='date',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='completion_date',
        ),
        migrations.RemoveField(
            model_name='correctivetask',
            name='comments',
        ),
    ]
