"""
Agrega el estado 'D' (Deshabilitado) con el id 3, que es el que el resto del código asume.

Un INSERT con id explícito NO avanza la secuencia de la columna identidad: PostgreSQL solo la
consume cuando el id se omite. Al dejar la fila 3 con la secuencia todavía en 1, el siguiente
`Estado.objects.create()` recibía el id 1, después el 2 y al tercero pedía el 3, que ya existía:

    duplicate key value violates unique constraint "works4cdp_estado_pkey"
    DETAIL:  Key (id)=(3) already exists.

El síntoma era intermitente y engañoso: las secuencias no se revierten con el rollback de
transacción de cada prueba, así que en una base ya usada la secuencia ya había pasado el 3 y no
fallaba nada. Solo aparecía en una base recién migrada, y según el orden de las pruebas.

Por eso, después de insertar, se sincroniza la secuencia con el id máximo real.
"""
from django.db import migrations


def add_deshabilitado_state(apps, schema_editor):
    Estado = apps.get_model('works4cdp', 'Estado')
    Estado.objects.get_or_create(id=3, defaults={'estado_nombre': 'D'})
    _sincronizar_secuencia(schema_editor)


def remove_deshabilitado_state(apps, schema_editor):
    Estado = apps.get_model('works4cdp', 'Estado')
    Estado.objects.filter(id=3).delete()
    _sincronizar_secuencia(schema_editor)


def _sincronizar_secuencia(schema_editor):
    """Deja la secuencia de works4cdp_estado.id en el id máximo existente.

    `is_called = true` (tercer argumento de setval) hace que el próximo nextval devuelva max(id) + 1.
    Si la tabla quedara vacía, max(id) es NULL y setval fallaría, así que se usa 1 con
    `is_called = false` para que el próximo id sea el 1. Es idempotente.
    """
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT setval(
                pg_get_serial_sequence('works4cdp_estado', 'id'),
                coalesce((SELECT max(id) FROM works4cdp_estado), 1),
                (SELECT count(*) > 0 FROM works4cdp_estado)
            );
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0009_correctivetask_turno'),
    ]

    operations = [
        migrations.RunPython(add_deshabilitado_state, reverse_code=remove_deshabilitado_state),
    ]
