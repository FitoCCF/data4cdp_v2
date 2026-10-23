"""Pruebas de la lógica propia de los modelos (save, __str__)."""
import datetime

from django.test import TestCase
from django.utils import timezone

from works4cdp.tests import factories as f


class AssaySaveTests(TestCase):

    def setUp(self):
        h = f.make_hierarchy()
        self.sample = f.make_sample(h['equipment'])

    def test_timestamp_combina_fecha_y_hora_con_zona(self):
        assay = f.make_assay(self.sample, date=datetime.date(2026, 5, 1), time=datetime.time(13, 30))
        self.assertTrue(timezone.is_aware(assay.timestamp))
        self.assertEqual(assay.timestamp.date(), datetime.date(2026, 5, 1))
        self.assertEqual(assay.timestamp.time(), datetime.time(13, 30))

    def test_timestamp_usa_medianoche_si_no_hay_hora(self):
        assay = f.make_assay(self.sample, date=datetime.date(2026, 5, 1), time=None)
        self.assertEqual(assay.timestamp.time(), datetime.time(0, 0))

    def test_timestamp_se_actualiza_al_cambiar_fecha(self):
        assay = f.make_assay(self.sample, date=datetime.date(2026, 5, 1))
        assay.date = datetime.date(2026, 6, 2)
        assay.save()
        self.assertEqual(assay.timestamp.date(), datetime.date(2026, 6, 2))

    def test_peso_prod_es_peso_total_menos_tara(self):
        assay = f.make_assay(self.sample, tara=114.5, tweight=174.5, dweight=30.0)
        self.assertEqual(assay.pweight, 60.0)
        assay.tweight = 200.3
        assay.save()
        self.assertEqual(assay.pweight, 85.8)  # sin ruido binario (200.3 - 114.5 = 85.80000000000001)

    def test_peso_prod_se_conserva_si_falta_un_peso(self):
        assay = f.make_assay(self.sample, tara=10.0, pweight=7.0)
        self.assertEqual(assay.pweight, 7.0)

    def test_psol_se_calcula_desde_los_pesos(self):
        # (dweight / (tweight - tara)) * 100 = 30 / (110 - 10) * 100
        assay = f.make_assay(self.sample, tara=10.0, tweight=110.0, dweight=30.0)
        self.assertEqual(assay.pSol, 30.0)

    def test_psol_se_redondea_a_dos_decimales(self):
        assay = f.make_assay(self.sample, tara=0.0, tweight=3.0, dweight=1.0)
        self.assertEqual(assay.pSol, 33.33)

    def test_psol_manual_no_se_sobrescribe(self):
        assay = f.make_assay(self.sample, tara=10.0, tweight=110.0, dweight=30.0, pSol=55.5)
        self.assertEqual(assay.pSol, 55.5)

    def test_psol_no_se_calcula_si_peso_neto_no_es_positivo(self):
        assay = f.make_assay(self.sample, tara=10.0, tweight=10.0, dweight=5.0)
        self.assertIsNone(assay.pSol)

    def test_psol_no_se_calcula_si_falta_un_peso(self):
        assay = f.make_assay(self.sample, tara=10.0, tweight=110.0)
        self.assertIsNone(assay.pSol)


class StrTests(TestCase):

    def test_representaciones_de_texto(self):
        h = f.make_hierarchy()
        catalog = f.make_catalog('Lubricación')
        group = f.make_group('Grupo B')
        user = f.make_user(group=group)
        sample = f.make_sample(h['equipment'], tag='S1', name='Pulpa')

        self.assertEqual(str(catalog), 'Lubricación')
        self.assertEqual(str(f.make_task(catalog)), 'Lubricación')
        self.assertEqual(str(user), 'Ana Pérez')
        self.assertEqual(str(sample), 'S1 - Pulpa')
        self.assertEqual(str(f.make_estado('Realizada')), 'Realizada')
        self.assertIn('Grupo: Grupo B', str(f.make_calendar(group)))
