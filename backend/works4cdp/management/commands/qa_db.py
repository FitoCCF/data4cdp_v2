"""
Revisión de calidad de datos (QA) de la base real. SOLO LECTURA.

    python manage.py qa_db

Cada chequeo ejecuta una consulta dentro de una transacción `READ ONLY`, de modo que aunque hubiera
un error en el código, PostgreSQL rechazaría cualquier escritura. Imprime OK / AVISO por chequeo y
algunos ejemplos de los registros afectados.
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction

# (código, descripción, SQL que devuelve las filas problemáticas)
CHECKS = [
    ('ASSAY-01', 'Ensayos con chemical_id repetido (< 100000)', """
        SELECT chemical_id, count(*) FROM works4cdp_assay
        WHERE chemical_id < 100000 GROUP BY chemical_id HAVING count(*) > 1"""),
    ('ASSAY-02', 'Ensayos con chemical_id >= 100000 (timestamps Unix históricos)', """
        SELECT id, chemical_id, date FROM works4cdp_assay WHERE chemical_id >= 100000"""),
    ('ASSAY-03', 'Ensayos duplicados por clave natural (muestra, fecha, hora, instancia)', """
        SELECT sample_id, date, time, instance, count(*) FROM works4cdp_assay
        GROUP BY sample_id, date, time, instance HAVING count(*) > 1"""),
    ('ASSAY-04', 'Ensayos con fecha anterior a 2015 o futura', """
        SELECT id, date, sample_id FROM works4cdp_assay
        WHERE date < '2015-01-01' OR date > current_date"""),
    ('ASSAY-05', 'Ensayos sin muestra', """
        SELECT id, date FROM works4cdp_assay WHERE sample_id IS NULL"""),
    ('ASSAY-06', 'Ensayos con timestamp distinto de fecha + hora', """
        SELECT id, date, time, timestamp FROM works4cdp_assay
        WHERE date IS NOT NULL
          AND (timestamp AT TIME ZONE current_setting('TIMEZONE'))
              <> (date + coalesce(time, '00:00'::time))"""),
    ('ASSAY-07', 'Ensayos con %Sol fuera de 0..100', """
        SELECT id, "pSol" FROM works4cdp_assay WHERE "pSol" < 0 OR "pSol" > 100"""),
    ('ASSAY-08', 'Ensayos con pesos negativos o peso seco mayor que el neto', """
        SELECT id, tara, tweight, dweight FROM works4cdp_assay
        WHERE tara < 0 OR tweight < 0 OR dweight < 0
           OR (tweight IS NOT NULL AND tara IS NOT NULL AND dweight > tweight - tara)"""),
    ('TASKP-01', 'Tareas programadas huérfanas (sin plantilla ni correctiva)', """
        SELECT id, date FROM works4cdp_taskp WHERE task_id IS NULL AND corrective_task_id IS NULL"""),
    ('TASKP-02', 'Tareas reprogramadas sin fecha de reprogramación', """
        SELECT id, date FROM works4cdp_taskp WHERE rescheduled AND reschedule_date IS NULL"""),
    ('TASKP-03', 'reschedule_user_id que no corresponde a ningún usuario', """
        SELECT t.id, t.reschedule_user_id FROM works4cdp_taskp t
        LEFT JOIN works4cdp_user u ON u.id = t.reschedule_user_id
        WHERE t.reschedule_user_id IS NOT NULL AND u.id IS NULL"""),
    ('TASKP-04', 'Fecha que no coincide con el año registrado', """
        SELECT id, date, year FROM works4cdp_taskp WHERE extract(isoyear FROM date) <> year
          AND extract(year FROM date) <> year"""),
    # El id se toma del default real del modelo (ver _taskp_default_estado) para no quedar desfasado.
    ('ESTADO-01', 'El estado por defecto de TaskP no existe o no es "P" (Pendiente)', """
        SELECT {default_id} AS id, e.estado_nombre FROM (SELECT 1) x
        LEFT JOIN works4cdp_estado e ON e.id = {default_id}
        WHERE e.id IS NULL OR e.estado_nombre NOT IN ('Pendiente', 'P')"""),
    ('CAL-01', 'Calendario duplicado (misma fecha, grupo y turno)', """
        SELECT date, group_id, turn, count(*) FROM works4cdp_calendar
        WHERE group_id IS NOT NULL GROUP BY date, group_id, turn HAVING count(*) > 1"""),
    ('CAL-02', 'Calendario sin grupo ni usuario', """
        SELECT id, date FROM works4cdp_calendar WHERE group_id IS NULL AND id_user IS NULL"""),
    ('EQ-01', 'Equipos sin área asignada', """
        SELECT id, name, tag FROM works4cdp_equipment WHERE area_id IS NULL"""),
    ('SAMPLE-01', 'Muestras con tag repetido dentro del mismo equipo', """
        SELECT equipment_id, lower(tag), count(*) FROM works4cdp_sample
        GROUP BY equipment_id, lower(tag) HAVING count(*) > 1"""),
    ('SAMPLE-02', 'Muestras sin tag', """
        SELECT id, name, equipment_id FROM works4cdp_sample WHERE coalesce(trim(tag), '') = ''"""),
    ('USER-01', 'Usuarios de la app sin login de Django vinculado', """
        SELECT id, nombre, apellido FROM works4cdp_user WHERE auth_user_id IS NULL"""),
    ('DB-01', 'works4cdp_assay no es hypertable de TimescaleDB', """
        SELECT 'works4cdp_assay' WHERE NOT EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'works4cdp_assay')"""),
]

MAX_EXAMPLES = 5


class Command(BaseCommand):
    help = 'Chequeos de calidad de datos sobre la base actual (solo lectura).'

    def handle(self, *args, **options):
        warnings = 0
        for code, description, sql in CHECKS:
            rows = self._run_read_only(sql.format(default_id=self._taskp_default_estado()))
            if rows:
                warnings += 1
                self.stdout.write(self.style.WARNING(f'[AVISO] {code} {description}: {len(rows)}'))
                for row in rows[:MAX_EXAMPLES]:
                    self.stdout.write(f'          {row}')
            else:
                self.stdout.write(self.style.SUCCESS(f'[OK]    {code} {description}'))

        summary = f'{len(CHECKS)} chequeos, {warnings} con avisos.'
        self.stdout.write(self.style.WARNING(summary) if warnings else self.style.SUCCESS(summary))

    @staticmethod
    def _taskp_default_estado():
        """Id de estado que Django asigna por defecto a una TaskP nueva (entero, seguro para el SQL)."""
        from works4cdp.models import TaskP
        return int(TaskP._meta.get_field('estado').default)

    @staticmethod
    def _run_read_only(sql):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute(sql)
            return cursor.fetchall()
