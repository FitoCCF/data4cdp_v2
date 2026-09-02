# Habilita anotaciones de tipo diferidas para compatibilidad con versiones modernas de Python.
from __future__ import annotations

# Import del módulo de registro para trazas, avisos y errores del sistema.
import logging
# Import de utilidades del sistema operativo para leer variables de entorno.
import os
# Import de clases para manipulación y parseo de fechas y horas.
from datetime import datetime, time, date
# Import de tipos genéricos para anotaciones estáticas de funciones.
from typing import Any, Dict, List, Optional, Set, Tuple

# Import de la librería HTTP para realizar peticiones a la API de los Courier.
import requests
# Import del adaptador HTTP para configurar reintentos y tolerancia a fallos.
from requests.adapters import HTTPAdapter
# Import de la estrategia de reintentos con backoff exponencial de urllib3.
from urllib3.util.retry import Retry

# Import de transacciones de Django para garantizar operaciones atómicas en BD.
from django.db import transaction
# Import de utilidades de zona horaria de Django para generar timestamps conscientes de zona.
from django.utils import timezone
# Import de la configuración global de Django para verificar entornos (dev/prod).
from django.conf import settings

# Import de los modelos de base de datos de la aplicación works4cdp.
from works4cdp.models import Sample, Assay, Equipment

# Instanciamos el logger para este módulo.
logger = logging.getLogger(__name__)

# Mapa estático de IP por ID de equipo analizador Courier (Courier 1, 2, 5, 6).
EQUIPMENT_IP_MAP: Dict[int, str] = {
    5: "172.18.16.21",  # Courier 5 (Red Planta 172.18.16.x)
    6: "172.18.16.20",  # Courier 6 (Red Planta 172.18.16.x)
    2: "192.168.59.55", # Courier 2 (Red Planta 192.168.59.x)
    1: "192.168.59.53", # Courier 1 (Red Planta 192.168.59.x)
}

# Puerto por defecto donde corre el servicio CLB en cada analizador Courier.
API_PORT = 7000
# Ruta del endpoint que lee el archivo de texto generado por el Courier.
API_ENDPOINT = "/api/clb/file"


class CLBClient:
    """
    Cliente HTTP orientado a objetos para comunicarse con la API de los Courier.
    Incluye timeouts estrictos, reintentos automáticos y soporte explícito dev/prod.
    """

    def __init__(self, ip: str, port: int = API_PORT, timeout: int = 5, is_dev: Optional[bool] = None):
        # Guardamos la IP del equipo analizador.
        self.ip = ip
        # Guardamos el puerto de la API (7000).
        self.port = port
        # Timeout en segundos para no colgar el worker si el equipo está apagado.
        self.timeout = timeout
        # Construimos la URL base del analizador.
        self.base_url = f"http://{self.ip}:{self.port}{API_ENDPOINT}"
        
        # Determinamos si se activa el modo simulación (DEV) para desarrollo sin red de planta.
        if is_dev is not None:
            self.is_dev = is_dev
        else:
            # Revisa si settings de Django o variables de entorno activan la simulación.
            self.is_dev = getattr(settings, "MOCK_CLB", False) or os.getenv("MOCK_CLB", "false").lower() == "true"

        # Inicializamos la sesión HTTP con reintentos configurados.
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Configura una sesión requests con reintentos automáticos y backoff."""
        # Creamos una sesión HTTP reutilizable.
        session = requests.Session()
        # Definimos estrategia de 2 reintentos ante caídas transitorias de red (500, 502, 503, 504).
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        # Montamos el adaptador para peticiones HTTP.
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_tag_entries(self, tag: str) -> List[Dict[str, Any]]:
        """
        Consulta las mediciones del archivo de texto para una etiqueta (tag) dada.
        Retorna la lista de registros o lista vacía si hay error o no hay datos.
        """
        # Si el modo DEV está activo, devolvemos datos simulados para no bloquear pruebas.
        if self.is_dev:
            logger.info("Modo DEV activo: generando datos simulados para tag '%s'", tag)
            return self._generate_mock_data(tag)

        # Construimos la URL con el parámetro name=<tag>.
        url = f"{self.base_url}?name={tag}"
        logger.debug("Consultando Courier: %s", url)

        try:
            # Realizamos la petición HTTP GET con tiempo límite.
            response = self.session.get(url, timeout=self.timeout)
            # Verificamos que la respuesta HTTP sea 200 OK.
            response.raise_for_status()
            # Convertimos la respuesta JSON en diccionario.
            payload = response.json()
            # La API devuelve el contenido indexado por la clave en minúsculas.
            key = tag.lower()
            # Obtenemos la lista de mediciones o lista vacía si no existe.
            items = payload.get(key) or []
            return items
        except requests.RequestException as exc:
            # Registramos la advertencia si el equipo no responde o el archivo no existe.
            logger.warning("No se pudo obtener datos del Courier %s para tag '%s': %s", self.ip, tag, exc)
            # Filosofía Fail-Safe: retornamos lista vacía sin romper la ejecución.
            return []

    def _generate_mock_data(self, tag: str) -> List[Dict[str, Any]]:
        """Genera lecturas sintéticas representativas para pruebas locales."""
        # Obtenemos la fecha y hora actual para el mock.
        now = datetime.now()
        return [
            {
                "date": now.strftime("%d.%m.%Y"),
                "hour": now.strftime("%H:%M:%S"),
                "instance": 1,
                "n1fe": 1520,
                "n2cu": 840,
                "n3zn": 110,
                "n4mo": 42,
                "n5ech5": 12,
                "n6sc": 45,
                "n7ech7": 18,
                "a1fe": 15.20,
                "a2cu": 0.84,
                "a3zn": 0.11,
                "a4mo": 0.042,
                "a5a5": 1.10,
                "a6sol": 0.04,
                "a7a7": 0.18,
            }
        ]

    def close(self):
        """Cierra la sesión HTTP para liberar descriptores de socket."""
        self.session.close()


class AssayTransformer:
    """
    Transformador de datos: normaliza cadenas, parsea números, fechas y genera
    el campo timestamp consciente de zona horaria requerido por TimescaleDB.
    """

    @staticmethod
    def clean_string(value: Optional[str]) -> Optional[str]:
        """Normaliza valores nulos o centinelas ('N/A', '', espacios) a None."""
        if value is None:
            return None
        clean = str(value).strip()
        # Si está vacío o es centinela N/A, devolvemos None.
        if not clean or clean.upper() == "N/A":
            return None
        return clean

    @classmethod
    def parse_date(cls, value: Optional[str]) -> Optional[date]:
        """Convierte una cadena de fecha ('DD.MM.YYYY' o 'YYYY-MM-DD') a objeto date."""
        clean = cls.clean_string(value)
        if not clean:
            return None
        # Formatos soportados por los analizadores y APIs.
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(clean, fmt).date()
            except ValueError:
                continue
        logger.warning("Formato de fecha no reconocido recibido de API: '%s'", value)
        return None

    @classmethod
    def parse_time(cls, value: Optional[str]) -> Optional[time]:
        """Convierte una cadena de hora ('HH:MM:SS') a objeto time."""
        clean = cls.clean_string(value)
        if not clean:
            return None
        try:
            return datetime.strptime(clean, "%H:%M:%S").time()
        except ValueError:
            # Intento de respaldo para formato HH:MM si viniera sin segundos.
            try:
                return datetime.strptime(clean, "%H:%M").time()
            except ValueError:
                logger.warning("Formato de hora no reconocido recibido de API: '%s'", value)
                return None

    @classmethod
    def parse_int(cls, value: Any) -> Optional[int]:
        """Convierte de forma segura una entrada a entero estándar."""
        clean = cls.clean_string(value)
        if clean is None:
            return None
        try:
            # Primero convertimos a float por si viene como "12.0" y luego a int.
            return int(round(float(clean)))
        except (ValueError, TypeError):
            return None

    @classmethod
    def parse_float(cls, value: Any) -> Optional[float]:
        """Convierte de forma segura una entrada a número flotante."""
        clean = cls.clean_string(value)
        if clean is None:
            return None
        try:
            # Reemplaza comas decimales por puntos si aplicara.
            clean = clean.replace(",", ".")
            return float(clean)
        except (ValueError, TypeError):
            return None

    @classmethod
    def build_timestamp(cls, date_val: Optional[date], time_val: Optional[time]) -> Optional[datetime]:
        """
        Construye un objeto datetime timezone-aware para TimescaleDB.
        Se calcula FUERA de cualquier bucle para corregir el bug del script original.
        """
        if not date_val:
            return None
        # Si no hay hora registrada, usamos la medianoche como respaldo.
        t = time_val or time(0, 0, 0)
        # Combinamos fecha y hora en un datetime ingenuo.
        dt = datetime.combine(date_val, t)
        # Verificamos si ya tiene zona horaria; de lo contrario, aplicamos la de Django.
        if timezone.is_aware(dt):
            return dt
        return timezone.make_aware(dt)


class AssaySyncService:
    """
    Servicio orquestador: Realiza la conciliación delta e inserción idempotente
    en la tabla works4cdp_assay protegiendo datos manuales y la integridad histórica.
    """

    @classmethod
    def sync_equipment(cls, equipment_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Sincroniza los datos del Courier para un equipo específico y fecha dada.
        SOLO inserta registros nuevos. NO sobreescribe pesos manuales de laboratorio.
        """
        # Obtenemos la IP asignada al equipo analizador.
        ip = EQUIPMENT_IP_MAP.get(int(equipment_id))
        if not ip:
            msg = f"El equipo con ID {equipment_id} no tiene una dirección IP configurada."
            logger.error(msg)
            return {"status": "error", "message": msg, "inserted": 0}

        # Buscamos todas las muestras asociadas a este equipo que tengan tag válido.
        samples = Sample.objects.filter(equipment_id=equipment_id).exclude(tag__isnull=True).exclude(tag="")
        if not samples.exists():
            msg = f"No se encontraron muestras con 'tag' configuradas para el equipo {equipment_id}."
            logger.info(msg)
            return {"status": "ok", "message": msg, "inserted": 0}

        # Creamos un mapa rápido en memoria de tag en minúsculas hacia la instancia Sample.
        sample_map = {s.tag.lower(): s for s in samples}

        # Si no se pasó fecha objetivo, usamos la fecha de hoy.
        effective_date = target_date or timezone.localdate()

        # CONCILIACIÓN DELTA:
        # Cargamos las claves ya existentes en BD para este equipo y esta fecha.
        # Clave natural = (sample_id, date, time, instance)
        existing_keys: Set[Tuple[int, date, Optional[time], Optional[int]]] = set(
            Assay.objects.filter(
                sample__equipment_id=equipment_id,
                date=effective_date
            ).values_list("sample_id", "date", "time", "instance")
        )

        logger.debug("Claves existentes en BD para equipo %s en fecha %s: %d", equipment_id, effective_date, len(existing_keys))

        # Inicializamos el cliente HTTP hacia el Courier.
        client = CLBClient(ip=ip)
        # Lista donde acumularemos las nuevas instancias Assay a insertar en lote.
        new_assays: List[Assay] = []

        try:
            # Iteramos cada muestra del equipo.
            for tag, sample_obj in sample_map.items():
                # Obtenemos los registros del archivo plano del Courier vía API.
                raw_entries = client.fetch_tag_entries(tag)
                # Si el archivo está vacío o falló, continuamos de forma segura (Fail-Safe).
                if not raw_entries:
                    continue

                # Procesamos cada fila leída del archivo del Courier.
                for entry in raw_entries:
                    # Parseamos la fecha del registro.
                    entry_date = AssayTransformer.parse_date(entry.get("date"))
                    # Filtramos: Solo procesamos registros que coincidan exactamente con la fecha objetivo.
                    if not entry_date or entry_date != effective_date:
                        continue

                    # Parseamos la hora y la instancia.
                    entry_time = AssayTransformer.parse_time(entry.get("hour"))
                    entry_instance = AssayTransformer.parse_int(entry.get("instance"))

                    # Construimos la tupla de clave natural para deduplicación.
                    natural_key = (sample_obj.id, entry_date, entry_time, entry_instance)

                    # Si la clave ya está en BD o ya la aceptamos en este mismo lote, LA IGNORAMOS.
                    if natural_key in existing_keys:
                        continue

                    # Parseamos las leyes químicas (elementos de canal).
                    a1fe_val = AssayTransformer.parse_float(entry.get("a1fe"))
                    a2cu_val = AssayTransformer.parse_float(entry.get("a2cu"))
                    a3zn_val = AssayTransformer.parse_float(entry.get("a3zn"))
                    a4mo_val = AssayTransformer.parse_float(entry.get("a4mo"))
                    a5a5_val = AssayTransformer.parse_float(entry.get("a5a5"))
                    a6sol_val = AssayTransformer.parse_float(entry.get("a6sol") or entry.get("a6sc") or entry.get("a6"))
                    a7a7_val = AssayTransformer.parse_float(entry.get("a7a7") or entry.get("a7ins") or entry.get("a7"))

                    # Mapeo a campos de porcentajes usados en SamplingView (%Fe, %Cu, %Zn, %Mo, %Ins).
                    p_fe_val = AssayTransformer.parse_float(entry.get("pFe")) or a1fe_val
                    p_cu_val = AssayTransformer.parse_float(entry.get("pCu")) or a2cu_val
                    p_zn_val = AssayTransformer.parse_float(entry.get("pZn")) or a3zn_val
                    p_mo_val = AssayTransformer.parse_float(entry.get("pMo")) or a4mo_val
                    p_ins_val = AssayTransformer.parse_float(entry.get("pIns")) or a7a7_val

                    # Construimos el timestamp consciente de zona horaria para TimescaleDB.
                    ts_val = AssayTransformer.build_timestamp(entry_date, entry_time)

                    # Instanciamos el modelo Assay con solo los datos del analizador.
                    # NOTA DE SEGURIDAD: No definimos tara, tweight, dweight ni pSol para no alterar pesos de laboratorio.
                    assay_instance = Assay(
                        sample=sample_obj,
                        date=entry_date,
                        time=entry_time,
                        instance=entry_instance,
                        timestamp=ts_val,
                        # Conteos del detector Courier
                        n1fe=AssayTransformer.parse_int(entry.get("n1fe")),
                        n2cu=AssayTransformer.parse_int(entry.get("n2cu")),
                        n3zn=AssayTransformer.parse_int(entry.get("n3zn")),
                        n4mo=AssayTransformer.parse_int(entry.get("n4mo")),
                        n5ech5=AssayTransformer.parse_int(entry.get("n5ech5")),
                        n6sc=AssayTransformer.parse_int(entry.get("n6sc") or entry.get("n6w_sc") or entry.get("n6kpsc") or entry.get("n6")),
                        n7ech7=AssayTransformer.parse_int(entry.get("n7ech7")),
                        # Leyes calculadas del Courier
                        a1fe=a1fe_val,
                        a2cu=a2cu_val,
                        a3zn=a3zn_val,
                        a4mo=a4mo_val,
                        a5a5=a5a5_val,
                        a6sol=a6sol_val,
                        a7a7=a7a7_val,
                        # Campos visualizados en reporte de calibración (SamplingView.vue)
                        pFe=p_fe_val,
                        pCu=p_cu_val,
                        pZn=p_zn_val,
                        pMo=p_mo_val,
                        pIns=p_ins_val,
                    )

                    # Añadimos la nueva instancia a la lista de inserción.
                    new_assays.append(assay_instance)
                    # Registramos la clave para evitar duplicados en el mismo archivo.
                    existing_keys.add(natural_key)

            # Si hay registros legítimamente nuevos, los insertamos atómicamente en bloque.
            if new_assays:
                with transaction.atomic():
                    # bulk_create ejecuta un único INSERT eficiente para todos los registros.
                    Assay.objects.bulk_create(new_assays)
                logger.info("Se insertaron exitosamente %d nuevos ensayos para equipo %s", len(new_assays), equipment_id)

            return {
                "status": "ok",
                "message": f"Sincronización finalizada. Nuevos registros: {len(new_assays)}",
                "inserted": len(new_assays),
            }

        finally:
            # Cerramos la sesión HTTP al terminar la operación.
            client.close()

    @classmethod
    def sync_all_couriers(cls, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Sincroniza todos los analizadores configurados (Courier 1, 2, 5, 6).
        Útil para comandos batch, cron jobs o ejecución general del sistema.
        """
        total_inserted = 0
        results_by_equipment = {}

        # Iteramos cada ID de equipo configurado en el mapa de IPs.
        for eq_id in EQUIPMENT_IP_MAP.keys():
            res = cls.sync_equipment(equipment_id=eq_id, target_date=target_date)
            results_by_equipment[eq_id] = res
            total_inserted += res.get("inserted", 0)

        return {
            "status": "ok",
            "total_inserted": total_inserted,
            "details": results_by_equipment,
        }
