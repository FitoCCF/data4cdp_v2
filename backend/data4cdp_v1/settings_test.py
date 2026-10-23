"""
Configuración para ejecutar las pruebas:

    python manage.py test works4cdp --settings=data4cdp_v1.settings_test

Django crea una base de datos aparte (test_mydb) y la destruye al terminar; la base real no se toca.
"""
from .settings import *  # noqa: F401,F403 — se hereda toda la configuración real

# template1 del servidor tiene un problema de versión de collation (la imagen timescaledb es
# Alpine/musl) que impide clonarlo; template0 sí se puede usar.
DATABASES['default']['TEST'] = {'TEMPLATE': 'template0'}  # noqa: F405


class DisableMigrations(dict):
    """Hace que Django cree todas las tablas desde los modelos actuales, sin ejecutar migraciones."""

    def __contains__(self, app_label):
        return True

    def __getitem__(self, app_label):
        return None


# Las migraciones de works4cdp no se pueden aplicar en una base vacía (ver works4cdp/test_runner.py).
# Se desactivan para todas las apps porque works4cdp depende de auth_user: si solo works4cdp quedara
# sin migraciones, su tabla se crearía antes que auth_user y fallaría la clave foránea.
MIGRATION_MODULES = DisableMigrations()
TEST_RUNNER = 'works4cdp.test_runner.WorksTestRunner'

# Las pruebas que tocan los Courier sustituyen el cliente HTTP con unittest.mock; nunca salen a la red.
