from django.apps import apps
from django.contrib import admin

# Se registran todos los modelos de la app automáticamente. Antes solo había 9 registrados a mano
# y faltaban Sample, Assay, AssaysPsi, Calendar, TaskCatalog, TaskGroupAssignment y UserP.
for model in apps.get_app_config('works4cdp').get_models():
    if not admin.site.is_registered(model):
        admin.site.register(model)
