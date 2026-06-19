# Generated manually to add 'D' (Deshabilitado) state to Estado table

from django.db import migrations

def add_deshabilitado_state(apps, schema_editor):
    Estado = apps.get_model('works4cdp', 'Estado')
    # Get or create state with ID 3
    Estado.objects.get_or_create(id=3, defaults={'estado_nombre': 'D'})

def remove_deshabilitado_state(apps, schema_editor):
    Estado = apps.get_model('works4cdp', 'Estado')
    Estado.objects.filter(id=3).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0009_correctivetask_turno'),
    ]

    operations = [
        migrations.RunPython(add_deshabilitado_state, reverse_code=remove_deshabilitado_state),
    ]
