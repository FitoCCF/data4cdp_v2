"""
Pasa a PROTECT las tres claves que permitían borrar en cascada el registro de trabajo:
Equipment.system, Equipment.area y Task.equipment.

Antes, borrar un área se llevaba sus equipos, sus tareas y todas las ocurrencias de TaskP, incluidas
las ya marcadas como realizadas (medido el 2026-11-05: borrar `Molibdeno C1` destruía 979
ocurrencias, 191 de ellas en estado R).

on_delete es una regla de Django, no una restricción de PostgreSQL: esta migración NO cambia el
esquema ni toca una fila. Solo alinea el estado de migraciones con el modelo. El efecto se ve en
tiempo de ejecución, donde el borrado ahora levanta ProtectedError, que la API traduce a HTTP 409.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0019_taskp_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='works4cdp.area'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='works4cdp.system'),
        ),
        migrations.AlterField(
            model_name='task',
            name='equipment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='works4cdp.equipment'),
        ),
    ]
