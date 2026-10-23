"""
Runner de pruebas del proyecto (se activa desde data4cdp_v1/settings_test.py).

Problema que resuelve: la migración 0005 agrega un UniqueConstraint llamado `works4cdp_assay_pkey`,
el mismo nombre que PostgreSQL da por defecto a la clave primaria de `works4cdp_assay`. En la base
de producción la PK se recreó a mano como (id, timestamp) para TimescaleDB, pero en una base nueva
las migraciones fallan con 'relation "works4cdp_assay_pkey" already exists'.

Para las pruebas, la base de works4cdp se crea directamente desde los modelos (sin migraciones) y
ese constraint se renombra solo en memoria. No se modifica ninguna migración ni la base real.
"""
from django.test.runner import DiscoverRunner

ASSAY_PKEY_NAME = 'works4cdp_assay_pkey'
ASSAY_TEST_CONSTRAINT_NAME = 'works4cdp_assay_id_timestamp_uniq'


class WorksTestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        from works4cdp.models import Assay

        for constraint in Assay._meta.constraints:
            if constraint.name == ASSAY_PKEY_NAME:
                constraint.name = ASSAY_TEST_CONSTRAINT_NAME
        return super().setup_databases(**kwargs)
