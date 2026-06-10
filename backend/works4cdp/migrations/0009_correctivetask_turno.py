# Generated manually to add 'turno' to CorrectiveTask

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0008_remove_correctivetask_redundant_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='correctivetask',
            name='turno',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
