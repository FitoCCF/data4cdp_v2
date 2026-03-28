from django.db import models # Importa el módulo de base de datos de Django para definir modelos
from django.contrib.auth.models import User as AuthUser # Importa el modelo de usuario estándar de Django y lo renombra como AuthUser

# Modelo que define el estado en el que se puede encontrar una tarea (Pendiente, Realizada, etc.)
class Estado(models.Model):
    estado_nombre = models.CharField(max_length=50) # Campo de texto para el nombre del estado (máximo 50 caracteres)

    class Meta:
        ordering = ['-id'] # Ordena los estados de manera descendente según su ID por defecto
    
    def __str__(self):
        return self.estado_nombre # Al imprimir el objeto, mostrará el nombre del estado

# Modelo que representa una Planta de la operación
class Plant(models.Model):
    tag = models.CharField(max_length=10) # Código corto o identificador de la planta
    name = models.CharField(max_length=100) # Nombre completo de la planta
    description = models.TextField(null=True, blank=True) # Descripción larga, opcional (puede dejarse vacío)

    class Meta:
        ordering = ['-id'] # Orden descendente por ID

# Modelo que representa un Área específica dentro de una Planta
class Area(models.Model):
    name = models.CharField(max_length=100) # Nombre del área
    tag = models.CharField(max_length=10, null=True, blank=True) # Etiqueta opcional para el área
    description = models.TextField(null=True, blank=True) # Descripción detallada opcional
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE) # Clave foránea hacia Plant; si se borra la planta, se borra el área

    class Meta:
        ordering = ['-id']

# Modelo para agrupar equipos bajo un mismo Sistema operativo
class System(models.Model):
    tag = models.CharField(max_length=50, null=True, blank=True) # Etiqueta o código del sistema, opcional
    name = models.CharField(max_length=100) # Nombre del sistema
    description = models.TextField(null=True, blank=True) # Descripción del sistema, opcional

    class Meta:
        ordering = ['-id']

# Modelo que representa un Equipo físico específico
class Equipment(models.Model):
    tag = models.CharField(max_length=50, null=True, blank=True) # Etiqueta o número de serie del equipo
    name = models.CharField(max_length=100) # Nombre descriptivo del equipo
    description = models.TextField(null=True, blank=True) # Funcionalidad o detalle del equipo
    system = models.ForeignKey(System, on_delete=models.CASCADE) # Relación con el Sistema al que pertenece (borrado en cascada)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)  # Relación con el Área en la que se ubica

    class Meta:
        ordering = ['-id']

# Modelo maestro para definir las pautas o plantillas de Tareas de mantenimiento
class Task(models.Model):
    name = models.CharField(max_length=100) # Nombre de la tarea a realizar
    duration = models.IntegerField(null=True, blank=True) # Tiempo estimado en horas/minutos, opcional
    workers = models.IntegerField(null=True, blank=True) # Cantidad de trabajadores requeridos, opcional
    frequency = models.CharField(max_length=50, null=True, blank=True) # Frecuencia con la que se repite (ej: "Mensual")
    start_date = models.DateField(null=True, blank=True) # Fecha planificada para el primer inicio
    description = models.TextField(null=True, blank=True) # Descripción profunda de qué se debe hacer
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True) # Equipo al que se le aplicará la tarea
    procedure = models.TextField(null=True, blank=True) # Pasos detallados a seguir
    turn = models.CharField(max_length=10, null=True, blank=True) # Turno sugerido u obligatorio

    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return self.name

# Modelo para definir roles o Grupos Personalizados para los usuarios
class UserP(models.Model):
    name = models.CharField(max_length=20) # Nombre del grupo (Ej. "Supervisor", "Operador")
    
    def __str__(self):
        return self.name

# Modelo que extiende la información de usuario en el sistema
class User(models.Model):
    auth_user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, null=True, blank=True) # Vinculación 1 a 1 con el login de Django
    nombre = models.CharField(max_length=50) # Nombre de pila
    apellido = models.CharField(max_length=50) # Apellidos
    email = models.EmailField(unique=True) # Correo, que será único en el sistema
    rol = models.CharField(max_length=50, null=True, blank=True) # Rol textual
    group = models.ForeignKey(UserP, on_delete=models.CASCADE, null=True, blank=True) # Asignación al grupo personalizado

    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}" # Se visualizará "Nombre Apellido"

# Modelo que gestiona los turnos o excepciones calendarias de trabajadores y grupos
class Calendar(models.Model):
    year = models.IntegerField()  # Año del turno
    week = models.IntegerField()  # Semana del año asociada
    day = models.CharField(max_length=20)  # Día textual ("Lunes", "Martes")
    date = models.DateField()  # Fecha exacta
    turn = models.CharField(max_length=10, null=True, blank=True)  # Turno programado ("A", "B", "C")
    group = models.ForeignKey(UserP, on_delete=models.CASCADE, null=True, blank=True) # Afecta a este grupo completo si existe

    overtime = models.IntegerField(default=0) # Horas extra planificadas (default 0)

    user = models.ForeignKey( # Excepción específica para un solo usuario en lugar de grupo
        User,
        on_delete=models.SET_NULL, # Si borran al usuario, esto queda en NULL (no se borra el registro de calendario)
        null=True,
        blank=True,
        related_name="Exception_calendar", # Nombre de acceso inverso (user.Exception_calendar.all())
        db_column="id_user" # Se nombra la columna real de la BD 'id_user'
    )

    class Meta:
        ordering = ['-date', 'group'] # Ordenados por fecha y grupo

    def __str__(self):
        tipo = f"Grupo: {self.group}" if self.group else f"Usuario: {self.user}"
        return f"{self.date} - {tipo} ({self.turn})"

# Modelo que representa la Ejecución Programada de una Tarea (Tarea a realizar en una fecha concreta)
class TaskP(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE) # Plantilla base de la tarea de la que hereda
    
    # --- DATOS DE PROGRAMACIÓN ORIGINAL ---
    year = models.IntegerField()              # Año en el que se programó ejecutar
    week = models.IntegerField()              # Semana en que toca ejecutar
    day = models.CharField(max_length=20)     # Nombre del día
    date = models.DateField()                 # Fecha exacta planificada originally
    
    # --- DATOS DE EJECUCIÓN REAL ---
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, default=1) # Vincula al modelo de estados; Default = 1 (Pendiente)
    completion_date = models.DateTimeField(null=True, blank=True)           # Cuándo se completó en realidad
    comments = models.TextField(null=True, blank=True)                      # Notas puestas por el operador al terminar
    
    # --- CONTROL DE EXCEPCIONES Y REPROGRAMACIÓN ---
    rescheduled = models.BooleanField(default=False)                        # Booleano que marca si esta tarea fue atrasada
    reschedule_date = models.DateField(null=True, blank=True)               # Para cuándo se movió la tarea
    reschedule_reason = models.TextField(null=True, blank=True)             # Por qué se movió (ej. falta de repuestos)
    reschedule_user_id = models.IntegerField(null=True, blank=True)         # ID de quien dio la orden de moverla
    
    group = models.ForeignKey(UserP, on_delete=models.SET_NULL, null=True, blank=True) # Operador/Grupo designado específicamente para esto

    is_permanent_reschedule = models.BooleanField(default=False, null=True, blank=True) # Si el cambio de fecha afecta a todas las futuras de la plantilla

    priority = models.IntegerField(null=True, blank=True, default=1)        # Prioridad de ejecución

    class Meta:
        ordering = ['-id']

# Asigna la tarea a un evento específico del calendario
class TaskGroupAssignment(models.Model):
    taskp = models.ForeignKey(TaskP, on_delete=models.CASCADE) # La tarea planificada
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE) # El registro de calendario que indica quién/cuándo

    class Meta:
        ordering = ['-id']

# Modelo para tareas correctivas imprevistas (fallas, roturas en el momento)
class CorrectiveTask(models.Model):
    year = models.IntegerField(null=True, blank=True) # Año de ocurrencia
    week = models.IntegerField(null=True, blank=True) # Semana de ocurrencia
    day = models.CharField(max_length=20, null=True, blank=True) # Día de ocurrencia
    date = models.DateField(null=True, blank=True) # Fecha exacta
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE) # Equipo que se rompió/falló
    description = models.TextField() # Descripción del incidente
    creation_date = models.DateField() # Fecha de reporte
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE) # Estado (ej: En Reparación)
    priority = models.IntegerField() # Nivel de criticidad
    created_by_user = models.ForeignKey(User, on_delete=models.CASCADE) # Quien lo reportó
    completion_date = models.DateField(null=True, blank=True) # Cuándo se solucionó
    root_cause = models.TextField(null=True, blank=True) # Causa raíz diagnosticada
    comments = models.TextField(null=True, blank=True) # Notas sobre cómo se reparó

    class Meta:
        ordering = ['-id']

# Modelo para identificar muestras físicas extraídas
class Sample(models.Model):
    tag = models.CharField(max_length=50) # Etiqueta de frasco/muestra
    name = models.CharField(max_length=50) # Nombre de la muestra (ej. Pulpa)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="samples") # De qué equipo salió (permite eq.samples.all())
    sn = models.CharField(max_length=4, null=True, blank=True) # Serial number, opcional

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.tag} - {self.name}"

# Modelo que registra los valores analizados para las muestras en laboratorios (Análisis Químico y Físico)
class Assay(models.Model):
    date = models.DateField(null=True, blank=True) # Fecha de ensayo
    time = models.TimeField(null=True, blank=True) # Hora de ensayo
    instance = models.IntegerField(null=True, blank=True) # Contador de iteración del ensayo
    
    # Lecturas enteras de elementos/componentes (Hierro, Cobre, Zinc, Molibdeno...)
    n1fe = models.IntegerField(null=True, blank=True) 
    n2cu = models.IntegerField(null=True, blank=True)
    n3zn = models.IntegerField(null=True, blank=True)
    n4mo = models.IntegerField(null=True, blank=True)
    n5ech5 = models.IntegerField(null=True, blank=True)
    n6sc = models.IntegerField(null=True, blank=True)
    n7ech7 = models.IntegerField(null=True, blank=True)
    
    # Porcentajes calculados de elementos químicos
    pFe = models.FloatField(null=True, blank=True)
    pCu = models.FloatField(null=True, blank=True)
    pZn = models.FloatField(null=True, blank=True)
    pMo = models.FloatField(null=True, blank=True)
    pIns = models.FloatField(null=True, blank=True) # Insoluble
    pSol = models.FloatField(null=True, blank=True) # Soluble
    
    # Pesos en balanza
    tara = models.FloatField(null=True, blank=True) # Peso recipiente (tara)
    tweight = models.FloatField(null=True, blank=True) # Peso bruto
    dweight = models.FloatField(null=True, blank=True) # Peso seco
    pweight = models.FloatField(null=True, blank=True) # Peso producto final
    chemical_id = models.IntegerField(null=True, blank=True) # ID o código del químico
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, null=True, blank=True) # La muestra física
    
    # Más campos flotantes de análisis
    a1fe = models.FloatField(null=True, blank=True)
    a2cu = models.FloatField(null=True, blank=True)
    a3zn = models.FloatField(null=True, blank=True)
    a4mo = models.FloatField(null=True, blank=True)
    a5a5 = models.FloatField(null=True, blank=True)
    a6sol = models.FloatField(null=True, blank=True)
    a7a7 = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # Usuario que capturó los datos
    meta_user = models.CharField(max_length=50, null=True, blank=True) # Metadatos de usuario en texto plano

    class Meta:
        ordering = ['-id']

# Modelo para ensayos de granulometría (Tamaño de partícula - Particle Size Indicator)
class AssaysPsi(models.Model):
    date = models.DateField(null=True, blank=True) # Fecha del granulométrico
    time = models.TimeField(null=True, blank=True) # Hora
    instance = models.IntegerField(null=True, blank=True) # Iteración
    
    # Pesos base
    tara = models.FloatField(null=True, blank=True) # Peso tara
    tweight = models.FloatField(null=True, blank=True) # Peso total
    dweight = models.FloatField(null=True, blank=True) # Peso en seco
    psolid = models.FloatField(null=True, blank=True) # Porcentaje de sólidos
    
    # Porcentajes de material retenido en distintas mallas de criba (Malla 48, 65, 100...)
    pW48 = models.FloatField(null=True, blank=True)
    pW65 = models.FloatField(null=True, blank=True)
    pW100 = models.FloatField(null=True, blank=True)
    pW150 = models.FloatField(null=True, blank=True)
    pW200 = models.FloatField(null=True, blank=True)
    pW325 = models.FloatField(null=True, blank=True)
    pW400 = models.FloatField(null=True, blank=True)
    
    # Estadísticas derivadas
    aAvg = models.FloatField(null=True, blank=True) # Promedio
    aSD = models.FloatField(null=True, blank=True) # Desviación estándar
    aDensity = models.FloatField(null=True, blank=True) # Densidad
    aSol = models.FloatField(null=True, blank=True) # Sólidos
    
    # Valores de pase (pasantes) por mallas
    aP48 = models.FloatField(null=True, blank=True)
    aP65 = models.FloatField(null=True, blank=True)
    aP100 = models.FloatField(null=True, blank=True)
    aP150 = models.FloatField(null=True, blank=True)
    aP200 = models.FloatField(null=True, blank=True)
    aP325 = models.FloatField(null=True, blank=True)
    aP400 = models.FloatField(null=True, blank=True)
    
    P80 = models.FloatField(null=True, blank=True) # Tamaño al que pasa el 80% del material
    P50 = models.FloatField(null=True, blank=True) # Tamaño al que pasa el 50% del material (mediana)
    
    # Cálculos adicionales para tamaño por malla
    pP48 = models.FloatField(null=True, blank=True)
    pP65 = models.FloatField(null=True, blank=True)
    pP100 = models.FloatField(null=True, blank=True)
    pP150 = models.FloatField(null=True, blank=True)
    pP200 = models.FloatField(null=True, blank=True)
    pP325 = models.FloatField(null=True, blank=True)
    pP400 = models.FloatField(null=True, blank=True)
    
    # Distribución en micras (μm) - Análisis fraccional
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # Analista
    meta_user = models.CharField(max_length=50, null=True, blank=True) # Metadatos en texto
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, null=True, blank=True) # Muestra evaluada
    turn = models.CharField(max_length=10, null=True, blank=True) # Turno en que se hizo el análisis

    class Meta:
        ordering = ['-id']
