# Generated manually to migrate scheduling/status fields of CorrectiveTask to TaskP instances

from django.db import migrations
import datetime

def migrate_corrective_tasks(apps, schema_editor):
    CorrectiveTask = apps.get_model('works4cdp', 'CorrectiveTask')
    TaskP = apps.get_model('works4cdp', 'TaskP')
    
    for ct in CorrectiveTask.objects.all():
        # Check if there is already an associated TaskP to avoid duplicate creation
        if not TaskP.objects.filter(corrective_task=ct).exists():
            year = ct.year if ct.year is not None else 2026
            week = ct.week if ct.week is not None else 1
            day = ct.day if ct.day else 'Lunes'
            date = ct.date
            
            if not date:
                if ct.creation_date:
                    date = ct.creation_date
                else:
                    date = datetime.date.today()
            
            # For completion_date conversion from DateField to DateTimeField
            comp_dt = None
            if ct.completion_date:
                comp_dt = datetime.datetime.combine(ct.completion_date, datetime.time.min)
            
            # Create TaskP instance mapping all scheduling and status information
            TaskP.objects.create(
                task=None,
                corrective_task=ct,
                year=year,
                week=week,
                day=day,
                date=date,
                estado=ct.estado,
                completion_date=comp_dt,
                comments=ct.comments,
                priority=ct.priority,
            )

def rollback_corrective_tasks(apps, schema_editor):
    TaskP = apps.get_model('works4cdp', 'TaskP')
    for tp in TaskP.objects.filter(corrective_task__isnull=False):
        ct = tp.corrective_task
        ct.year = tp.year
        ct.week = tp.week
        ct.day = tp.day
        ct.date = tp.date
        ct.estado = tp.estado
        if tp.completion_date:
            ct.completion_date = tp.completion_date.date()
        else:
            ct.completion_date = None
        ct.comments = tp.comments
        ct.save()

class Migration(migrations.Migration):

    dependencies = [
        ('works4cdp', '0006_taskp_corrective_task_alter_taskp_task_correctivetask_name'),
    ]

    operations = [
        migrations.RunPython(migrate_corrective_tasks, rollback_corrective_tasks),
    ]
