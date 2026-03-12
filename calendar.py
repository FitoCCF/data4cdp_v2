from datetime import datetime, timedelta


def calcular_semana_extendida(fecha):
    year = fecha.isocalendar()[0]
    week_iso = fecha.isocalendar()[1]
    return week_iso + 6 + ((year - 1963) * 52)


def generar_vista_previa_diccionario(inicio, fin, patron_fijo):
    """
    Genera un diccionario de prueba para verificar la lógica de Calendar.
    """
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    NUM_GRUPOS = 7
    longitud_patron = len(patron_fijo)
    desfase_por_grupo = longitud_patron / NUM_GRUPOS

    # Estructura: { 'Grupo_1': [registros...], 'Grupo_2': [...] }
    vista_previa = {}

    for i in range(NUM_GRUPOS):
        id_grupo_userp = i + 1  # Simulando IDs de la tabla UserP (antes Group)
        nombre_grupo = f"UserP_ID_{id_grupo_userp}"
        vista_previa[nombre_grupo] = []

        inicio_patron = round(i * desfase_por_grupo)
        patron_reordenado = patron_fijo[inicio_patron:] + patron_fijo[:inicio_patron]

        fecha_actual = inicio
        index = 0

        # Generamos solo los primeros 10 días para no saturar la consola
        dias_a_mostrar = 49
        while fecha_actual <= fin and index < dias_a_mostrar:
            turno = patron_reordenado[index % len(patron_reordenado)]

            registro = {
                "year": fecha_actual.year,
                "week": calcular_semana_extendida(fecha_actual),
                "day": dias_semana[fecha_actual.weekday()],
                "date": fecha_actual.strftime("%Y-%m-%d"),
                "turn": turno,
                "group_id": id_grupo_userp,  # FK a UserP
                "overtime": 0,
                "user_id": None  # NULL por ser preventivo grupal
            }

            vista_previa[nombre_grupo].append(registro)
            fecha_actual += timedelta(days=1)
            index += 1

    return vista_previa


# --- CONFIGURACIÓN DE PRUEBA ---
inicio_periodo = datetime(2026, 3, 9)
fin_periodo = datetime(2026, 4, 26)

patron_fijo = [
    "N", "N", "N", "x", "x", "x", "D",
    "D", "D", "D", "D", "x", "x", "x",
    "x", "N", "N", "N", "N", "x", "x",
    "x", "x", "D", "D", "D", "D", "x",
    "x", "x", "x", "N", "N", "N", "N",
    "N", "x", "x", "x", "D", "D", "D",
    "D", "D", "x", "x", "x", "N", "N"
]

# --- EJECUCIÓN DE VISTA PREVIA ---
if __name__ == "__main__":
    datos_prueba = generar_vista_previa_diccionario(inicio_periodo, fin_periodo, patron_fijo)

    print("=== VISTA PREVIA DE LLENADO DE CALENDAR (UserP) ===\n")
    for grupo, registros in datos_prueba.items():
        print(f"--- {grupo} ---")
        for r in registros:
            # Formato scannable para verificar rotación de turnos
            print(f"Fecha: {r['date']} | Día: {r['day'][:3]} | Sem_Ext: {r['week']} | Turno: [{r['turn']}]")
        print("\n")