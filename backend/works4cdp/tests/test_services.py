"""Pruebas del servicio de sincronización con los Courier (clb_syncer). La red siempre se simula."""
import datetime
from unittest import mock

import requests
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from works4cdp.models import Assay
from works4cdp.services.clb_syncer import (
    AssaySyncService, AssayTransformer, CLBClient, assay_sort_key, natural_sort_key,
)
from works4cdp.tests import factories as f


class AssayTransformerTests(SimpleTestCase):

    def test_clean_string(self):
        self.assertIsNone(AssayTransformer.clean_string(None))
        self.assertIsNone(AssayTransformer.clean_string('   '))
        self.assertIsNone(AssayTransformer.clean_string('n/a'))
        self.assertEqual(AssayTransformer.clean_string(' 12 '), '12')

    def test_parse_date_formatos_soportados(self):
        esperado = datetime.date(2026, 3, 4)
        for texto in ('04.03.2026', '2026-03-04', '04/03/2026', '2026/03/04'):
            self.assertEqual(AssayTransformer.parse_date(texto), esperado, texto)

    def test_parse_date_invalida(self):
        self.assertIsNone(AssayTransformer.parse_date('31.02.2026'))
        self.assertIsNone(AssayTransformer.parse_date('ayer'))

    def test_parse_time(self):
        self.assertEqual(AssayTransformer.parse_time('08:15:30'), datetime.time(8, 15, 30))
        self.assertEqual(AssayTransformer.parse_time('08:15'), datetime.time(8, 15))
        self.assertIsNone(AssayTransformer.parse_time('25:00'))

    def test_parse_int_redondea_y_tolera_basura(self):
        self.assertEqual(AssayTransformer.parse_int('12.0'), 12)
        self.assertEqual(AssayTransformer.parse_int('12.6'), 13)
        self.assertIsNone(AssayTransformer.parse_int('abc'))
        self.assertIsNone(AssayTransformer.parse_int(''))

    def test_parse_float_acepta_coma_decimal(self):
        self.assertEqual(AssayTransformer.parse_float('0,84'), 0.84)
        self.assertEqual(AssayTransformer.parse_float(1.5), 1.5)
        self.assertIsNone(AssayTransformer.parse_float('x'))

    def test_build_timestamp(self):
        ts = AssayTransformer.build_timestamp(datetime.date(2026, 1, 2), None)
        self.assertTrue(timezone.is_aware(ts))
        self.assertEqual(ts.time(), datetime.time(0, 0))
        self.assertIsNone(AssayTransformer.build_timestamp(None, datetime.time(1, 0)))


class SortKeyTests(SimpleTestCase):

    def test_orden_natural(self):
        tags = ['C_01_S10', 'C_01_S2', 'c_01_s01']
        self.assertEqual(sorted(tags, key=natural_sort_key), ['c_01_s01', 'C_01_S2', 'C_01_S10'])

    def test_assay_sort_key_tolera_muestra_hora_e_instancia_nulas(self):
        assay = Assay(sample=None, instance=None, time=None)
        self.assertEqual(assay_sort_key(assay), ([''], 0, datetime.time(0, 0)))


class CLBClientTests(SimpleTestCase):

    def test_modo_dev_devuelve_datos_simulados_sin_red(self):
        client = CLBClient('10.0.0.1', is_dev=True)
        with mock.patch.object(client.session, 'get') as get:
            rows = client.fetch_tag_entries('c_01_s01', target_date=datetime.date(2026, 1, 2))
        get.assert_not_called()
        self.assertEqual(rows[0]['date'], '02.01.2026')

    def test_error_de_red_devuelve_lista_vacia(self):
        client = CLBClient('10.0.0.1', is_dev=False)
        with mock.patch.object(client.session, 'get', side_effect=requests.ConnectionError('caído')):
            self.assertEqual(client.fetch_tag_entries('c_01_s01'), [])

    def test_lee_la_lista_por_tag_en_minusculas(self):
        client = CLBClient('10.0.0.1', is_dev=False)
        response = mock.Mock()
        response.json.return_value = {'c_01_s01': [{'n1fe': 1}]}
        with mock.patch.object(client.session, 'get', return_value=response) as get:
            self.assertEqual(client.fetch_tag_entries('C_01_S01'), [{'n1fe': 1}])
        self.assertIn('name=C_01_S01', get.call_args.args[0])


def courier_row(fecha='15.01.2026', hora='08:00:00', instancia=1, **lecturas):
    return {'date': fecha, 'hour': hora, 'instance': instancia, 'n1fe': '100', 'a2cu': '0,84', **lecturas}


class AssaySyncServiceTests(TestCase):

    def setUp(self):
        h = f.make_hierarchy(plant_tag='C1', plant_name='Concentradora 1')
        self.equipment = h['equipment']
        # Se reemplaza el mapa de IPs reales por uno de prueba y se restaura al terminar cada test.
        self.ip_map = {self.equipment.id: '10.0.0.1'}
        patcher = mock.patch.dict('works4cdp.services.clb_syncer.EQUIPMENT_IP_MAP', self.ip_map, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.s2 = f.make_sample(self.equipment, tag='C_01_S2')
        self.s10 = f.make_sample(self.equipment, tag='C_01_S10')
        self.fecha = datetime.date(2026, 1, 15)

    def sync(self, rows_by_tag):
        fake = lambda tag, target_date=None: rows_by_tag.get(tag, [])
        with mock.patch.object(CLBClient, 'fetch_tag_entries', side_effect=fake):
            return AssaySyncService.sync_equipment(self.equipment.id, target_date=self.fecha)

    def test_inserta_y_asigna_chemical_id_en_orden_natural(self):
        result = self.sync({'c_01_s10': [courier_row()], 'c_01_s2': [courier_row()]})
        self.assertEqual(result['inserted'], 2)
        primero = Assay.objects.get(sample=self.s2)
        segundo = Assay.objects.get(sample=self.s10)
        # Concentradora 1 sin datos previos: la serie arranca en 26001; S2 va antes que S10.
        self.assertEqual((primero.chemical_id, segundo.chemical_id), (26001, 26002))
        self.assertEqual(primero.a2cu, 0.84)
        self.assertIsNone(primero.pCu)  # campos de laboratorio quedan para llenado manual

    def test_es_idempotente(self):
        rows = {'c_01_s2': [courier_row()]}
        self.sync(rows)
        result = self.sync(rows)
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(Assay.objects.count(), 1)

    def test_ignora_lecturas_de_otra_fecha_y_duplicadas_en_el_mismo_archivo(self):
        result = self.sync({'c_01_s2': [courier_row(), courier_row(), courier_row(fecha='14.01.2026')]})
        self.assertEqual(result['found_in_api'], 2)
        self.assertEqual(result['inserted'], 1)

    def test_asigna_codigo_a_ensayos_previos_sin_chemical_id(self):
        f.make_assay(self.s2, date=self.fecha, chemical_id=None)
        result = self.sync({})
        self.assertEqual(result['updated_chemical_ids'], 1)
        self.assertEqual(Assay.objects.get().chemical_id, 26001)

    def test_continua_la_serie_existente_e_ignora_timestamps_unix(self):
        f.make_assay(self.s2, date=datetime.date(2026, 1, 1), chemical_id=26500)
        f.make_assay(self.s2, date=datetime.date(2026, 1, 1), time=datetime.time(9, 0), chemical_id=1741018740)
        self.sync({'c_01_s2': [courier_row()]})
        self.assertEqual(Assay.objects.get(date=self.fecha).chemical_id, 26501)

    def test_equipo_sin_ip_configurada(self):
        result = AssaySyncService.sync_equipment(999999, target_date=self.fecha)
        self.assertEqual(result['status'], 'error')

    def test_equipo_sin_muestras(self):
        from works4cdp.services import clb_syncer
        otro = f.make_equipment(self.equipment.system, name='Sin muestras')
        clb_syncer.EQUIPMENT_IP_MAP[otro.id] = '10.0.0.2'  # se restaura con patcher.stop
        result = AssaySyncService.sync_equipment(otro.id, target_date=self.fecha)
        self.assertEqual((result['status'], result['inserted']), ('ok', 0))


class NextChemicalIdTests(TestCase):

    def test_base_por_planta_sin_datos(self):
        c1 = f.make_plant(tag='C1', name='Concentradora 1')
        c2 = f.make_plant(tag='C2', name='Concentradora 2')
        self.assertEqual(AssaySyncService.get_next_chemical_id_for_plant(plant=c1), 26001)
        self.assertEqual(AssaySyncService.get_next_chemical_id_for_plant(plant=c2), 10001)

    def test_base_por_equipo_sin_planta(self):
        self.assertEqual(AssaySyncService.get_next_chemical_id_for_plant(equipment_id=1), 26001)
        self.assertEqual(AssaySyncService.get_next_chemical_id_for_plant(equipment_id=5), 10001)
