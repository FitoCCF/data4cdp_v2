import psycopg2
from datetime import datetime, timedelta

# Conexión a la base de datos PostgreSQL

# connection = psycopg2.connect(
#     host="localhost",  # Cambiar según sea necesario
#     database="mydb",
#     user="myuser",
#     password="mypassword",
#     port=5432
# )
# cursor = connection.cursor()

# Parámetros iniciales de la tarea
xweek = 3231  # Número de semana inicial para 2025
year = 2025
initial_week = xweek - ((year - 1963) * 52) - 6  # Cálculo de la semana inicial
start_date = datetime.strptime("2024-12-30", "%Y-%m-%d")
frequency = 2  # Días entre repeticiones

# Obtener los días de la semana para el cálculo
DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Crear registros para la tabla works4cdp_taskp
records = []
current_date = start_date
current_week = initial_week

while current_date.year <= 2025:  # Generar registros para todo el año 2025
    day_name = DAYS_OF_WEEK[current_date.weekday()]

    # Crear un registro para la tarea
    record = (
        year,  # Año actual
        current_week,  # Número de semana
        day_name,  # Día de la semana
        current_date.strftime("%Y-%m-%d"),  # Fecha
        "A",  # Turno
        1,  # Usuario
        False,  # Rescheduled
        None,  # Reschedule reason
        None,  # Reschedule date
        None,  # Reschedule user id
        2,  # Estado ID
        1,  # Task ID
        2   # Equipment ID
    )

    records.append(record)

    # Incrementar la fecha según la frecuencia
    current_date += timedelta(days=frequency)

    # Actualizar el número de semana si es necesario
    week_number = current_date.isocalendar()[1]
    if week_number != current_week:
        current_week = week_number

# Insertar registros en la base de datos
insert_query = """
    INSERT INTO works4cdp_taskp (
        year, week, day, date, turn, usuario, rescheduled, reschedule_reason,
        reschedule_date, reschedule_user_id, estado_id, task_id, equipment_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# cursor.executemany(insert_query, records)
# connection.commit()
#
# # Confirmar y cerrar conexión
# print(f"{len(records)} registros insertados correctamente en works4cdp_taskp.")
# cursor.close()
# connection.close()
