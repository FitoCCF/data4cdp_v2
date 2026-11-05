"""
Agrega TaskP.updated_at: marca de último cambio, para sincronizar hacia la lista de SharePoint que se
edita desde Power Apps sin recorrer las ~7500 tareas en cada corrida.

Al agregar una columna auto_now, Django rellena las filas existentes con la hora de la migración
(schema_editor._effective_default usa datetime.now() para auto_now/auto_now_add, aunque el campo sea
null=True). Eso dejaría las ~7500 tareas marcadas como "modificadas ahora" y la primera
sincronización intentaría publicar el histórico completo, así que después de agregar la columna se
vuelve a NULL: solo lo que se modifique desde ahora entra en la ventana de sincronización. Para
publicar algo anterior se usa la ventana explícita del comando de sincronización.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0018_taskp_estado_default_pendiente'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskp',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.RunSQL(
            sql="UPDATE works4cdp_taskp SET updated_at = NULL;",
            # Al revertir se elimina la columna completa, así que no hay nada que restaurar.
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
