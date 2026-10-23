"""Pruebas de reglas de validación y representación en los serializers."""
from django.test import TestCase

from works4cdp.serializers import AssaySerializer, CalendarSerializer, TaskPSerializer
from works4cdp.tests import factories as f


class AssaySerializerTests(TestCase):

    def setUp(self):
        h = f.make_hierarchy()
        self.sample = f.make_sample(h['equipment'])

    def test_rechaza_chemical_id_repetido(self):
        f.make_assay(self.sample, chemical_id=26001)
        serializer = AssaySerializer(data={'sample_id': self.sample.id, 'date': '2026-01-16', 'chemical_id': 26001})
        self.assertFalse(serializer.is_valid())
        self.assertIn('chemical_id', serializer.errors)
        self.assertIn('26001', str(serializer.errors['chemical_id'][0]))

    def test_permite_conservar_su_propio_chemical_id_al_editar(self):
        assay = f.make_assay(self.sample, chemical_id=26001)
        serializer = AssaySerializer(assay, data={'chemical_id': 26001, 'pCu': 1.2}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_chemical_id_nulo_es_valido(self):
        serializer = AssaySerializer(data={'sample_id': self.sample.id, 'date': '2026-01-16', 'chemical_id': None})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_nan_se_serializa_como_null(self):
        assay = f.make_assay(self.sample, a2cu=float('nan'))
        self.assertIsNone(AssaySerializer(assay).data['a2cu'])

    def test_sample_se_lee_anidado_y_se_escribe_por_id(self):
        assay = f.make_assay(self.sample)
        data = AssaySerializer(assay).data
        self.assertEqual(data['sample']['tag'], self.sample.tag)
        self.assertNotIn('sample_id', data)  # write_only

    def test_timestamp_es_solo_lectura(self):
        serializer = AssaySerializer(data={'sample_id': self.sample.id, 'date': '2026-01-16', 'timestamp': '1999-01-01T00:00:00Z'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        assay = serializer.save()
        self.assertEqual(assay.timestamp.year, 2026)


class TaskPSerializerTests(TestCase):

    def test_lee_relaciones_anidadas_y_escribe_ids(self):
        h = f.make_hierarchy()
        estado = f.make_estado()
        task = f.make_task(f.make_catalog(), h['equipment'])
        group = f.make_group()
        serializer = TaskPSerializer(data={
            'task_id': task.id, 'estado_id': estado.id, 'group_id': group.id,
            'year': 2026, 'week': 10, 'day': 'Lunes', 'date': '2026-03-02',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = TaskPSerializer(serializer.save()).data
        self.assertEqual(data['task']['id'], task.id)
        self.assertEqual(data['task']['name'], 'Calibración')
        self.assertEqual(data['estado']['estado_nombre'], 'Pendiente')
        self.assertEqual(data['group']['name'], 'Grupo A')

    def test_estado_id_es_obligatorio(self):
        serializer = TaskPSerializer(data={'year': 2026, 'week': 10, 'day': 'Lunes', 'date': '2026-03-02'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('estado_id', serializer.errors)


class CalendarSerializerTests(TestCase):

    def test_user_id_y_group_id_son_obligatorios_al_crear(self):
        # Documenta el comportamiento actual: aunque el modelo permite user/group nulos,
        # la API exige ambos al crear un registro de calendario.
        serializer = CalendarSerializer(data={'year': 2026, 'week': 10, 'day': 'Lunes', 'date': '2026-03-02'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)
        self.assertIn('group_id', serializer.errors)
