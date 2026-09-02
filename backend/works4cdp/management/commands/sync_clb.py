# Permite ejecutar este comando con: python manage.py sync_clb [--equipment ID] [--date YYYY-MM-DD]
from __future__ import annotations

# Import de datetime para parsear la fecha opcional pasada por argumento.
from datetime import datetime
# Import de la clase base para comandos de administración de Django.
from django.core.management.base import BaseCommand, CommandParser
# Import de utilidades de fecha local de Django.
from django.utils import timezone

# Importamos nuestro servicio de sincronización de Couriers.
from works4cdp.services.clb_syncer import AssaySyncService, EQUIPMENT_IP_MAP


class Command(BaseCommand):
    # Texto de ayuda que se muestra al ejecutar: python manage.py sync_clb --help
    help = "Sincroniza datos de ensayos desde los analizadores Courier (API CLB) hacia la base de datos."

    def add_arguments(self, parser: CommandParser) -> None:
        """Define los argumentos de línea de comandos admitidos."""
        # Argumento opcional para sincronizar un equipo específico (1, 2, 5 o 6).
        parser.add_argument(
            "--equipment",
            type=int,
            choices=list(EQUIPMENT_IP_MAP.keys()),
            help=f"ID del equipo a sincronizar. Opciones disponibles: {list(EQUIPMENT_IP_MAP.keys())}",
        )
        # Argumento opcional para especificar la fecha objetivo en formato ISO (YYYY-MM-DD).
        parser.add_argument(
            "--date",
            type=str,
            help="Fecha en formato YYYY-MM-DD a sincronizar (por defecto hoy).",
        )

    def handle(self, *args, **options) -> None:
        """Punto de entrada cuando se ejecuta el comando."""
        # Obtenemos el ID de equipo si fue proporcionado.
        equipment_id = options.get("equipment")
        # Obtenemos la cadena de fecha si fue proporcionada.
        date_str = options.get("date")

        # Parseamos la fecha si viene en los argumentos, de lo contrario usamos la fecha local de hoy.
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Formato de fecha inválido: {date_str}. Use YYYY-MM-DD."))
                return
        else:
            target_date = timezone.localdate()

        self.stdout.write(self.style.NOTICE(f"Iniciando sincronización para fecha: {target_date}"))

        # Si el usuario especificó un equipo, sincronizamos solo ese analizador.
        if equipment_id:
            self.stdout.write(f"Sincronizando únicamente equipo {equipment_id}...")
            # Llamamos al servicio de sincronización para ese equipo.
            result = AssaySyncService.sync_equipment(equipment_id=equipment_id, target_date=target_date)
            # Verificamos si la operación fue exitosa.
            if result.get("status") == "ok":
                self.stdout.write(self.style.SUCCESS(f"✅ {result.get('message')} (Insertados: {result.get('inserted')})"))
            else:
                self.stderr.write(self.style.ERROR(f"❌ Error: {result.get('message')}"))
        else:
            # Si no especificó equipo, sincronizamos todos los Couriers configurados (como el script original).
            self.stdout.write("Sincronizando todos los analizadores Courier configurados...")
            # Invocamos la sincronización global.
            result = AssaySyncService.sync_all_couriers(target_date=target_date)
            total = result.get("total_inserted", 0)
            self.stdout.write(self.style.SUCCESS(f"✅ Sincronización global finalizada. Total registros insertados: {total}"))
            # Mostramos el desglose por equipo.
            for eq_id, detail in result.get("details", {}).items():
                self.stdout.write(f"  - Equipo {eq_id}: {detail.get('message')}")
