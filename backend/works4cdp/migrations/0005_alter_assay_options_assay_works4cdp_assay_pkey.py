"""
Clave primaria compuesta (id, timestamp) de works4cdp_assay, para TimescaleDB.

CONTEXTO (reconstruido el 2026-11-05)
-------------------------------------
`works4cdp_assay` se convirtió a mano en un hypertable de TimescaleDB. TimescaleDB exige que la
columna de partición (`timestamp`) forme parte de toda clave única de la tabla, así que hubo que
reemplazar la PK original sobre `(id)` por una compuesta sobre `(id, timestamp)`.

Ese reemplazo se hizo con un ALTER TABLE manual que nunca quedó escrito en una migración. De la
operación solo se versionó la mitad visible: un UniqueConstraint declarado en `Assay.Meta` con el
mismo nombre que la restricción de la base, cuyo único objetivo era que `makemigrations` dejara de
querer recrear la pkey tradicional en cada corrida.

El problema: `works4cdp_assay_pkey` NO es un nombre elegido, es el que PostgreSQL le da
automáticamente a la clave primaria de `works4cdp_assay`. En la base de producción el ALTER TABLE
manual había liberado ese nombre antes, así que no chocaba. En una base nueva, `CreateModel` crea la
PK sobre `(id)` con ese mismo nombre y el AddConstraint original fallaba con:

    relation "works4cdp_assay_pkey" already exists

Es decir: el proyecto no se podía levantar de cero, y las pruebas necesitaban
`migrate works4cdp 0005 --fake` para armar su base.

QUÉ HACE AHORA
--------------
Escribe el paso manual. `SeparateDatabaseAndState` separa lo que Django cree de lo que se le pide a
PostgreSQL, porque acá hacen falta distintas cosas:

- Para el estado de Django: el UniqueConstraint de siempre. Es lo que calla a `makemigrations` y
  mantiene el historial compatible con las bases donde esta migración ya figura aplicada.
- Para la base: liberar el nombre tirando la PK sobre `(id)` y volver a crearlo como PK compuesta
  `(id, timestamp)`, que es exactamente lo que tiene la base de producción
  (verificado: `contype = 'p'`, `PRIMARY KEY (id, "timestamp")`).

En una base donde esta migración ya está aplicada (producción) NO se ejecuta nada: Django no vuelve
a correr una migración registrada. El cambio solo afecta a bases nuevas.

LO QUE ESTA MIGRACIÓN NO HACE
-----------------------------
No convierte la tabla en hypertable: no corre `create_hypertable()`. Una base nueva queda con la PK
compuesta pero con la tabla sin particionar. Versionar la conversión es una decisión aparte (implica
exigir la extensión TimescaleDB en cualquier entorno donde se migre, incluidas las pruebas).

Nota sobre el revés: al revertir se restituye la PK sobre `(id)`, lo que en una base donde la tabla
YA es hypertable va a fallar, porque TimescaleDB rechaza una clave única sin la columna de partición.
Es el comportamiento correcto — revertir esto en producción no es una operación válida.
"""
from django.db import migrations, models

# Se nombra la restricción igual que antes a propósito: así la base nueva queda idéntica a la de
# producción. IF EXISTS porque el nombre puede venir de la PK implícita (base nueva) o no existir
# (base ya intervenida a mano).
SQL_PK_COMPUESTA = """
    ALTER TABLE works4cdp_assay DROP CONSTRAINT IF EXISTS works4cdp_assay_pkey;
    ALTER TABLE works4cdp_assay
      ADD CONSTRAINT works4cdp_assay_pkey PRIMARY KEY (id, "timestamp");
"""

# ADD PRIMARY KEY impone NOT NULL en sus columnas, así que al revertir no se restaura la nulabilidad
# de `timestamp`. No hace falta: el modelo la declara null=True y Django no la verifica contra la base.
SQL_PK_SIMPLE = """
    ALTER TABLE works4cdp_assay DROP CONSTRAINT IF EXISTS works4cdp_assay_pkey;
    ALTER TABLE works4cdp_assay
      ADD CONSTRAINT works4cdp_assay_pkey PRIMARY KEY (id);
"""


class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0004_assay_timestamp'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assay',
            options={'ordering': ['-timestamp']},
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddConstraint(
                    model_name='assay',
                    constraint=models.UniqueConstraint(fields=('id', 'timestamp'),
                                                       name='works4cdp_assay_pkey'),
                ),
            ],
            database_operations=[
                migrations.RunSQL(sql=SQL_PK_COMPUESTA, reverse_sql=SQL_PK_SIMPLE),
            ],
        ),
    ]
