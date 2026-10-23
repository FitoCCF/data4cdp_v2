"""Funciones para crear datos de prueba con valores por defecto razonables."""
import datetime

from works4cdp.models import (
    Area, Assay, Calendar, CorrectiveTask, Equipment, Estado, Plant, Sample,
    System, Task, TaskCatalog, TaskGroupAssignment, TaskP, User, UserP,
)


def make_plant(tag='C1', name='Concentradora 1'):
    return Plant.objects.create(tag=tag, name=name)


def make_area(plant, name='Flotación', tag='FL'):
    return Area.objects.create(plant=plant, name=name, tag=tag)


def make_system(name='Analizadores', tag='AN'):
    return System.objects.create(name=name, tag=tag)


def make_equipment(system, area=None, name='Courier', tag='CR'):
    return Equipment.objects.create(system=system, area=area, name=name, tag=tag)


def make_sample(equipment, tag='C_01_S01', name='Alimentación'):
    return Sample.objects.create(equipment=equipment, tag=tag, name=name)


def make_assay(sample, date=datetime.date(2026, 1, 15), time=datetime.time(8, 0), **fields):
    return Assay.objects.create(sample=sample, date=date, time=time, **fields)


def make_estado(nombre='Pendiente'):
    return Estado.objects.create(estado_nombre=nombre)


def make_catalog(name='Calibración'):
    return TaskCatalog.objects.create(name=name)


def make_task(catalog, equipment=None, turn='A'):
    return Task.objects.create(task_catalog=catalog, equipment=equipment, turn=turn)


def make_group(name='Grupo A'):
    return UserP.objects.create(name=name)


def make_user(group=None, email='ana@example.com', nombre='Ana', apellido='Pérez'):
    return User.objects.create(nombre=nombre, apellido=apellido, email=email, group=group)


def make_taskp(estado, task=None, corrective_task=None, date=datetime.date(2026, 3, 2), week=10, year=2026):
    return TaskP.objects.create(
        task=task, corrective_task=corrective_task, estado=estado,
        year=year, week=week, day='Lunes', date=date,
    )


def make_corrective(equipment, user, creation_date=datetime.date(2026, 3, 2), name='Falla bomba'):
    return CorrectiveTask.objects.create(
        equipment=equipment, created_by_user=user, description='Rotura',
        creation_date=creation_date, priority=1, name=name,
    )


def make_calendar(group, date=datetime.date(2026, 3, 2), week=10, year=2026, turn='A'):
    return Calendar.objects.create(group=group, date=date, week=week, year=year, day='Lunes', turn=turn)


def assign(taskp, calendar):
    return TaskGroupAssignment.objects.create(taskp=taskp, calendar=calendar)


def make_hierarchy(plant_tag='C1', plant_name='Concentradora 1'):
    """Crea Planta > Área > Equipo (con su Sistema) y devuelve un dict con todo."""
    plant = make_plant(tag=plant_tag, name=plant_name)
    area = make_area(plant)
    system = make_system()
    equipment = make_equipment(system, area)
    return {'plant': plant, 'area': area, 'system': system, 'equipment': equipment}
