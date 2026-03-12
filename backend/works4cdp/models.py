from django.db import models
from django.contrib.auth.models import User as AuthUser

class Estado(models.Model):
    estado_nombre = models.CharField(max_length=50)

    class Meta:
        ordering = ['-id']

class Plant(models.Model):
    tag = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

class Area(models.Model):
    name = models.CharField(max_length=100)
    tag = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']

class System(models.Model):
    tag = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

class Equipment(models.Model):
    tag = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)  # Nuevo campo agregado

    class Meta:
        ordering = ['-id']

class Task(models.Model):
    name = models.CharField(max_length=100)
    duration = models.IntegerField(null=True, blank=True)
    workers = models.IntegerField(null=True, blank=True)
    frequency = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True)
    procedure = models.TextField(null=True, blank=True)
    turn = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        ordering = ['-id']

class UserP(models.Model):
    name = models.CharField(max_length=20)

class User(models.Model):
    auth_user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=50, null=True, blank=True)
    group = models.ForeignKey(UserP, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-id']



class Calendar(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)  # Si User se elimina, también se borra User
    #user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    year = models.IntegerField()  # Año
    week = models.IntegerField()
    day = models.CharField(max_length=20)  # Día de la semana (Ejemplo: "Lunes")
    date = models.DateField()  # Fecha en formato YYYY-MM-DD
    #state = models.CharField(null=True, max_length=10)  # Estado (Ejemplo: "Activo", "Inactivo")
    turn = models.CharField(max_length=10, null=True, blank=True)  # Turno (Ejemplo: "A", "B", "C")
    group = models.ForeignKey(UserP, on_delete=models.CASCADE, null=True, blank=True)

    overtime = models.IntegerField(default=0)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="Exception_calendar",
        db_column="id_user"
    )

    class Meta:
        ordering = ['-date', 'group']

    def __str__(self):
        tipo = f"Grupo: {self.group}" if self.group else f"Usuario: {self.user}"
        return f"{self.date} - {tipo} ({self.turn})"
    #def __str__(self):
    #    return f"{self.user.nombre} - {self.date} - {self.turn}"


class TaskGroupAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']


class TaskP(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    year = models.IntegerField()
    week = models.IntegerField()
    day = models.CharField(max_length=20)
    date = models.DateField()
  #  turn = models.CharField(max_length=10, null=True, blank=True)
   # usuario = models.IntegerField(null=True, blank=True)
    #group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    rescheduled = models.BooleanField(default=False)
    reschedule_reason = models.TextField(null=True, blank=True)
    reschedule_date = models.DateField(null=True, blank=True)
    reschedule_user_id = models.IntegerField(null=True, blank=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    priority = models.IntegerField(null=True, blank=True)
    #equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-id']


class CorrectiveTask(models.Model):
    year = models.IntegerField(null=True, blank=True)
    week = models.IntegerField(null=True, blank=True)
    day = models.CharField(max_length=20, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    #group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    description = models.TextField()
    creation_date = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    priority = models.IntegerField()
    created_by_user = models.ForeignKey(User, on_delete=models.CASCADE)
    completion_date = models.DateField(null=True, blank=True)
    root_cause = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    #turn = models.CharField(max_length=10, null=True, blank=True)  # Turno (Ejemplo: "A", "B", "C")

    class Meta:
        ordering = ['-id']


class Sample(models.Model):
    tag = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="samples")
    sn = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.tag} - {self.name}"


class Assay(models.Model):
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    instance = models.IntegerField(null=True, blank=True)
    n1fe = models.IntegerField(null=True, blank=True)
    n2cu = models.IntegerField(null=True, blank=True)
    n3zn = models.IntegerField(null=True, blank=True)
    n4mo = models.IntegerField(null=True, blank=True)
    n5ech5 = models.IntegerField(null=True, blank=True)
    n6sc = models.IntegerField(null=True, blank=True)
    n7ech7 = models.IntegerField(null=True, blank=True)
    pFe = models.FloatField(null=True, blank=True)
    pCu = models.FloatField(null=True, blank=True)
    pZn = models.FloatField(null=True, blank=True)
    pMo = models.FloatField(null=True, blank=True)
    pIns = models.FloatField(null=True, blank=True)
    pSol = models.FloatField(null=True, blank=True)
    tara = models.FloatField(null=True, blank=True)
    tweight = models.FloatField(null=True, blank=True)
    dweight = models.FloatField(null=True, blank=True)
    pweight = models.FloatField(null=True, blank=True)
    chemical_id = models.IntegerField(null=True, blank=True)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, null=True, blank=True)
    a1fe = models.FloatField(null=True, blank=True)
    a2cu = models.FloatField(null=True, blank=True)
    a3zn = models.FloatField(null=True, blank=True)
    a4mo = models.FloatField(null=True, blank=True)
    a5a5 = models.FloatField(null=True, blank=True)
    a6sol = models.FloatField(null=True, blank=True)
    a7a7 = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    meta_user = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-id']

class VTaskP(models.Model):
    planta = models.CharField(max_length=255)
    sistema = models.CharField(max_length=255)
    equipo = models.CharField(max_length=255)
    descripcion = models.TextField()
    tarea_descripcion = models.TextField()
    tag = models.CharField(max_length=100)
    id_task = models.IntegerField()
    semana = models.IntegerField()
    fecha = models.DateField()
    dia_semana = models.CharField(max_length=20)
    estado = models.CharField(max_length=50)
    turno = models.CharField(max_length=10)
    id_taskp = models.IntegerField(primary_key=True)  # ID de la tabla original TaskP

    class Meta:
        managed = False  # No permite que Django administre la vista
        db_table = "vtaskp"  # Nombre exacto de la vista en PostgreSQL
        ordering = ['-id_taskp']

class AssaysPsi(models.Model):
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    instance = models.IntegerField(null=True, blank=True)
    tara = models.FloatField(null=True, blank=True)
    tweight = models.FloatField(null=True, blank=True)
    dweight = models.FloatField(null=True, blank=True)
    psolid = models.FloatField(null=True, blank=True)
    pW48 = models.FloatField(null=True, blank=True)
    pW65 = models.FloatField(null=True, blank=True)
    pW100 = models.FloatField(null=True, blank=True)
    pW150 = models.FloatField(null=True, blank=True)
    pW200 = models.FloatField(null=True, blank=True)
    pW325 = models.FloatField(null=True, blank=True)
    pW400 = models.FloatField(null=True, blank=True)
    aAvg = models.FloatField(null=True, blank=True)
    aSD = models.FloatField(null=True, blank=True)
    aDensity = models.FloatField(null=True, blank=True)
    aSol = models.FloatField(null=True, blank=True)
    aP48 = models.FloatField(null=True, blank=True)
    aP65 = models.FloatField(null=True, blank=True)
    aP100 = models.FloatField(null=True, blank=True)
    aP150 = models.FloatField(null=True, blank=True)
    aP200 = models.FloatField(null=True, blank=True)
    aP325 = models.FloatField(null=True, blank=True)
    aP400 = models.FloatField(null=True, blank=True)
    P80 = models.FloatField(null=True, blank=True)
    P50 = models.FloatField(null=True, blank=True)
    pP48 = models.FloatField(null=True, blank=True)
    pP65 = models.FloatField(null=True, blank=True)
    pP100 = models.FloatField(null=True, blank=True)
    pP150 = models.FloatField(null=True, blank=True)
    pP200 = models.FloatField(null=True, blank=True)
    pP325 = models.FloatField(null=True, blank=True)
    pP400 = models.FloatField(null=True, blank=True)
    an_50_um = models.FloatField(null=True, blank=True)
    a50_100_um = models.FloatField(null=True, blank=True)
    a100_150_um = models.FloatField(null=True, blank=True)
    a150_200_um = models.FloatField(null=True, blank=True)
    a200_250_um = models.FloatField(null=True, blank=True)
    a250_300_um = models.FloatField(null=True, blank=True)
    a300_350_um = models.FloatField(null=True, blank=True)
    a350_400_um = models.FloatField(null=True, blank=True)
    a400_450_um = models.FloatField(null=True, blank=True)
    a450_500_um = models.FloatField(null=True, blank=True)
    a500_550_um = models.FloatField(null=True, blank=True)
    a550_600_um = models.FloatField(null=True, blank=True)
    a600_650_um = models.FloatField(null=True, blank=True)
    a650_700_um = models.FloatField(null=True, blank=True)
    a700_750_um = models.FloatField(null=True, blank=True)
    a750_800_um = models.FloatField(null=True, blank=True)
    a800_850_um = models.FloatField(null=True, blank=True)
    a850_900_um = models.FloatField(null=True, blank=True)
    a900_950_um = models.FloatField(null=True, blank=True)
    a950_1000_um = models.FloatField(null=True, blank=True)
    a1000_n_um = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    meta_user = models.CharField(max_length=50, null=True, blank=True)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, null=True, blank=True)
    turn = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        ordering = ['-id']
