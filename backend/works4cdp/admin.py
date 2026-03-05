from django.contrib import admin
from .models import (
    Estado, Plant, Area, System, Equipment, Task, TaskP, User, CorrectiveTask
)

admin.site.register(Estado)
admin.site.register(Plant)
admin.site.register(Area)
admin.site.register(System)
admin.site.register(Equipment)
admin.site.register(Task)
admin.site.register(TaskP)
admin.site.register(User)
admin.site.register(CorrectiveTask)

