# Generated manually to handle schema changes

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0005_alter_assay_options_assay_works4cdp_assay_pkey'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskp',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='works4cdp.task'),
        ),
        migrations.AddField(
            model_name='taskp',
            name='corrective_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taskp_instances', to='works4cdp.correctivetask'),
        ),
        migrations.AddField(
            model_name='correctivetask',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
