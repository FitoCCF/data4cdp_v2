"""Pruebas de los filtros y el orden genéricos de las grillas (grid_filters, grid-values, ordering)."""
import datetime
import json

from rest_framework.test import APITestCase

from works4cdp.tests import factories as f


def gf(spec):
    return {'grid_filters': json.dumps(spec)}


class GridFiltersTests(APITestCase):

    def setUp(self):
        self.system = f.make_system()
        # tag: 'A', 'B', '' (texto vacío) y None (NULL): las dos formas de "vacío" que hay en la base real.
        for i, tag in enumerate(['A', 'B', '', None]):
            f.make_equipment(self.system, name=f'Eq{i}', tag=tag)

    def count(self, spec, endpoint='equipments'):
        response = self.client.get(f'/api/{endpoint}/', gf(spec))
        self.assertEqual(response.status_code, 200, response.data)
        return response.data['count']

    def test_in(self):
        self.assertEqual(self.count({'tag': {'in': ['A', 'B']}}), 2)

    def test_vacias_sola_incluye_null_y_texto_vacio(self):
        # Antes: `tag__in=` se ignoraba y devolvía todo.
        self.assertEqual(self.count({'tag': {'in': [], 'empty': True}}), 2)

    def test_vacias_mas_un_valor_es_un_o(self):
        # Antes: `tag__in=A&tag__isnull=True` se combinaba con AND y devolvía 0.
        self.assertEqual(self.count({'tag': {'in': ['A'], 'empty': True}}), 3)

    def test_nada_seleccionado_no_devuelve_filas(self):
        self.assertEqual(self.count({'tag': {'in': []}}), 0)

    def test_not_in_conserva_vacias(self):
        self.assertEqual(self.count({'tag': {'not_in': ['A']}}), 3)

    def test_not_in_excluyendo_vacias(self):
        self.assertEqual(self.count({'tag': {'not_in': ['A'], 'empty': True}}), 1)

    def test_valor_con_coma_no_se_parte(self):
        f.make_equipment(self.system, name='Bomba, norte', tag='X')
        self.assertEqual(self.count({'name': {'in': ['Bomba, norte']}}), 1)

    def test_columnas_se_combinan_con_and(self):
        self.assertEqual(self.count({'tag': {'in': ['A', 'B']}, 'name': {'in': ['Eq0']}}), 1)

    def test_campo_fuera_de_filterset_fields_si_se_filtra(self):
        # Antes AssayViewSet ignoraba pCu, chemical_id, etc. porque no estaban en filterset_fields.
        sample = f.make_sample(f.make_equipment(self.system))
        f.make_assay(sample, pCu=0.84, chemical_id=26001)
        f.make_assay(sample, time=datetime.time(9, 0), pCu=1.2, chemical_id=26002)
        self.assertEqual(self.count({'pCu': {'in': ['0.84']}}, 'assays'), 1)
        self.assertEqual(self.count({'chemical_id': {'not_in': ['26001']}}, 'assays'), 1)

    def test_fk_por_nombre_de_columna_id(self):
        estado = f.make_estado()
        otro = f.make_estado('Realizada')
        task = f.make_task(f.make_catalog())
        f.make_taskp(estado, task=task)
        f.make_taskp(otro, task=task)
        self.assertEqual(self.count({'estado_id': {'in': [str(estado.id)]}}, 'taskp'), 1)

    def test_booleanos_como_los_muestra_la_grilla(self):
        estado = f.make_estado()
        task = f.make_task(f.make_catalog())
        f.make_taskp(estado, task=task)
        reprogramada = f.make_taskp(estado, task=task)
        reprogramada.rescheduled = True
        reprogramada.save()
        self.assertEqual(self.client.get('/api/taskp/grid-values/', {'field': 'rescheduled'}).data['values'], ['false', 'true'])
        self.assertEqual(self.count({'rescheduled': {'in': ['false']}}, 'taskp'), 1)
        self.assertEqual(self.count({'rescheduled': {'not_in': ['false']}}, 'taskp'), 1)

    def test_ruta_relacionada_declarada(self):
        h = f.make_hierarchy(plant_name='Concentradora 1')
        f.make_task(f.make_catalog('A'), h['equipment'])
        f.make_task(f.make_catalog('B'), None)
        self.assertEqual(self.count({'equipment__area__plant__name': {'in': ['Concentradora 1']}}, 'tasks'), 1)
        self.assertEqual(self.count({'equipment__area__plant__name': {'in': [], 'empty': True}}, 'tasks'), 1)

    def test_errores_devuelven_400(self):
        for spec in ({'no_existe': {'in': ['1']}},
                     {'area__plant__name': {'in': ['x']}},  # ruta relacionada no declarada
                     {'id': {'in': ['abc']}},
                     {'tag': ['A']},
                     {'tag': {'otra': []}}):
            self.assertEqual(self.client.get('/api/equipments/', gf(spec)).status_code, 400, spec)
        self.assertEqual(self.client.get('/api/equipments/', {'grid_filters': '{no json'}).status_code, 400)

    def test_convive_con_los_filtros_clasicos(self):
        otro = f.make_system('Bombas')
        f.make_equipment(otro, name='Eq9', tag='A')
        response = self.client.get('/api/equipments/', {'system': otro.id, **gf({'tag': {'in': ['A']}})})
        self.assertEqual(response.data['count'], 1)


class GridValuesTests(APITestCase):

    def setUp(self):
        self.system = f.make_system()
        f.make_equipment(self.system, name='Eq10', tag='A')
        f.make_equipment(self.system, name='Eq2', tag='A')
        f.make_equipment(self.system, name='Eq3', tag='')
        f.make_equipment(self.system, name='Eq4', tag=None)

    def values(self, **params):
        response = self.client.get('/api/equipments/grid-values/', params)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_valores_distintos_con_vacias_unificadas(self):
        data = self.values(field='tag')
        self.assertEqual(data['values'], ['', 'A'])
        self.assertFalse(data['truncated'])

    def test_filtrado_cruzado_ignora_la_propia_columna(self):
        filtros = json.dumps({'tag': {'in': ['A']}, 'name': {'in': ['Eq3']}})
        # La columna tag no se filtra por sí misma, pero sí por name.
        self.assertEqual(self.values(field='tag', grid_filters=filtros)['values'], [''])
        self.assertEqual(self.values(field='name', grid_filters=filtros)['values'], ['Eq10', 'Eq2'])

    def test_limite_y_busqueda(self):
        data = self.values(field='name', limit=2)
        self.assertEqual(len(data['values']), 2)
        self.assertTrue(data['truncated'])
        self.assertEqual(self.values(field='name', search='10')['values'], ['Eq10'])

    def test_respeta_parametros_fijos_de_la_vista(self):
        otro = f.make_system('Bombas')
        f.make_equipment(otro, name='Solo', tag='Z')
        self.assertEqual(self.values(field='tag', system=otro.id)['values'], ['Z'])

    def test_fechas_en_iso_y_fk_por_id(self):
        h = f.make_hierarchy()
        sample = f.make_sample(h['equipment'])
        f.make_assay(sample, date=datetime.date(2026, 3, 4))
        data = self.client.get('/api/assays/grid-values/', {'field': 'date'}).data
        self.assertEqual(data['values'], ['2026-03-04'])
        data = self.client.get('/api/assays/grid-values/', {'field': 'sample'}).data
        self.assertEqual(data['values'], [str(sample.id)])

    def test_errores(self):
        self.assertEqual(self.client.get('/api/equipments/grid-values/').status_code, 400)
        self.assertEqual(self.client.get('/api/equipments/grid-values/', {'field': 'nope'}).status_code, 400)
        self.assertEqual(self.client.get('/api/equipments/grid-values/', {'field': 'tag', 'limit': 'x'}).status_code, 400)


class GridOrderingTests(APITestCase):

    def test_ordena_por_cualquier_campo_con_desempate_por_pk(self):
        system = f.make_system()
        ids = [f.make_equipment(system, name='Igual', tag=t).id for t in ['b', 'a', 'b']]
        asc = [r['id'] for r in self.client.get('/api/equipments/', {'ordering': 'tag'}).data['results']]
        self.assertEqual(asc, [ids[1], ids[0], ids[2]])
        # 'tag' no estaba en ordering_fields de otras vistas; 'day' de TaskP tampoco: ahora se aceptan.
        desc = [r['id'] for r in self.client.get('/api/equipments/', {'ordering': '-tag'}).data['results']]
        self.assertEqual(desc[-1], ids[1])

    def test_ordena_por_ruta_relacionada_y_fk_id(self):
        estado = f.make_estado()
        h1 = f.make_hierarchy(plant_tag='Z', plant_name='Zeta')
        h2 = f.make_hierarchy(plant_tag='A', plant_name='Alfa')
        t1 = f.make_taskp(estado, task=f.make_task(f.make_catalog('X'), h1['equipment']))
        t2 = f.make_taskp(estado, task=f.make_task(f.make_catalog('Y'), h2['equipment']))
        res = self.client.get('/api/taskp/', {'ordering': 'task__equipment__area__plant__name'}).data['results']
        self.assertEqual([r['id'] for r in res], [t2.id, t1.id])
        self.assertEqual(self.client.get('/api/taskp/', {'ordering': '-estado_id'}).status_code, 200)

    def test_campo_invalido_se_ignora(self):
        self.assertEqual(self.client.get('/api/equipments/', {'ordering': 'no_existe'}).status_code, 200)
