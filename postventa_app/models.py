from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
import os
from django.core.files.storage import FileSystemStorage


class NombreOriginalStorage(FileSystemStorage):
    """Storage personalizado que preserva el nombre original del archivo"""
    def get_available_name(self, name, max_length=None):
        # Si el archivo ya existe, agrega un contador
        if self.exists(name):
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            
            # Buscar el próximo número disponible
            counter = 1
            while True:
                new_name = f'{file_root}_{counter}{file_ext}'
                full_path = os.path.join(dir_name, new_name) if dir_name else new_name
                if not self.exists(full_path):
                    return full_path
                counter += 1
        return name


def archivo_path(instance, filename):
    """Generar ruta para guardar archivo manteniendo el nombre original"""
    return f'evidencias/{filename}'


# ================================================================
# MODELO: PERFIL DE USUARIO
# ================================================================
class Perfil(models.Model):
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
    ROLES = [
        ('administrador', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('tecnico', 'Técnico'),
        ('propietario', 'Propietario'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES)
    rut = models.CharField(max_length=15, blank=True, null=True, verbose_name="RUT/DNI")
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    # Proyecto asignado (para supervisores)
    proyecto = models.ForeignKey(
        'Proyecto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervisores',
        verbose_name='Proyecto asignado'
    )

    def __str__(self):
        return f"{self.user.username} - {self.rol}"


def validate_rut(value: str):
    """Validación básica de RUT chileno.
    - Permite números, puntos, guion y K/k.
    - No valida dígito verificador matemáticamente (se normaliza en importación).
    """
    if value is None:
        return
    s = str(value).strip()
    if not s:
        return
    if not re.match(r"^[0-9.\-kK]+$", s):
        raise ValidationError("RUT inválido: use números, puntos y guion (ej: 12.345.678-9)")



# ================================================================
# MODELO: UNIDAD
# ================================================================
class Unidad(models.Model):
    id_unidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)  # Ej: Depto 101, Casa 5
    proyecto = models.ForeignKey('Proyecto', on_delete=models.CASCADE, related_name='unidades')
    cliente = models.ForeignKey('Propietario', on_delete=models.SET_NULL, null=True, blank=True, related_name='unidades')
    descripcion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'unidad'
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'

    def __str__(self):
        return f"{self.nombre}"



# ================================================================
# MODELO: ESPECIALIDAD
# ================================================================
class Especialidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'especialidad'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.nombre

# ================================================================
# MODELO 4: CATEGORÍA (SIMPLE)
# ================================================================
class Categoria(models.Model):
    """
    Tipo de falla o problema reportado (filtración, pintura, electricidad, etc.)
    Modelo simple solo para clasificación.
    """
    nombre = models.CharField(max_length=80, unique=True, verbose_name="Nombre de categoría")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ================================================================
# MODELO 2: PROPIETARIO (COMPLETO)
# ========================================
class Propietario(models.Model):
    def __str__(self):
        return f"{self.nombre} ({self.rut})"
    """
    Representa al propietario de una unidad que realiza reclamos postventa.
    Es el usuario final del sistema.
    """
    TIPO_PROPIETARIO = [
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica'),
    ]
    
    ESTADO_PROPIETARIO = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    # Vinculación con cuenta de usuario
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='propietario', verbose_name="Usuario del sistema")
    
    # Información básica
    nombre = models.CharField(max_length=120, verbose_name="Nombre completo")
    rut = models.CharField(max_length=12, verbose_name="RUT/DNI")
    tipo_propietario = models.CharField(max_length=10, choices=TIPO_PROPIETARIO, default='natural', verbose_name="Tipo de propietario")
    
    # Contacto
    email = models.EmailField(verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=30, verbose_name="Teléfono")
    telefono_alternativo = models.CharField(max_length=30, blank=True, null=True, verbose_name="Teléfono alternativo")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    
    # Propiedad/Vivienda
    proyecto = models.ForeignKey('Proyecto', on_delete=models.SET_NULL, null=True, blank=True, related_name='propietarios', verbose_name="Proyecto de vivienda")

# ================================================================
# MODELO 6: TECNICO
# ================================================================
# MODELO 2: CONSTRUCTORA
# ================================================================
class Constructora(models.Model):
    """
    Constructora responsable de proyectos.
    """
    id_constructora = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=15, unique=True)
    razon_social = models.CharField(max_length=150)
    nombre_fantasia = models.CharField(max_length=100, null=True, blank=True)
    email_contacto = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    sitio_web = models.CharField(max_length=200, null=True, blank=True)
    representante_legal = models.CharField(max_length=150, null=True, blank=True)
    estado = models.CharField(max_length=20, null=True, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'constructora'
        verbose_name = 'Constructora'
        verbose_name_plural = 'Constructoras'

    def __str__(self):
        return f"{self.razon_social}"


# ================================================================
# MODELO 3: PROYECTO
# ================================================================
class Proyecto(models.Model):
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    """
    Proyectos inmobiliarios.
    """
    id_proyecto = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del proyecto", default="")
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(null=True, blank=True)
    tipo_proyecto = models.CharField(max_length=50, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de inicio")
    fecha_entrega = models.DateField(null=True, blank=True)
    cantidad_unidades = models.IntegerField(null=True, blank=True)
    encargado = models.CharField(max_length=120, blank=True, null=True, verbose_name="Encargado del proyecto")
    telefono_encargado = models.CharField(max_length=30, blank=True, null=True, verbose_name="Teléfono encargado")
    ESTADO_CHOICES = [
        ("entregado", "Entregado"),
        ("garantia", "En Garantía"),
        ("finalizado", "Finalizado"),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="entregado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    constructora = models.ForeignKey(
        Constructora,
        on_delete=models.CASCADE,
        related_name='proyectos',
        verbose_name="Constructora",
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'proyecto'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ================================================================
# MODELO 4: RECLAMO
# ================================================================
class Reclamo(models.Model):
    @property
    def citas_activas(self):
        """Retorna las citas activas (pendiente, confirmada, en_curso) asociadas a este reclamo, ordenadas por fecha."""
        return self.citas.filter(estado__in=['pendiente', 'confirmada', 'en_curso']).order_by('fecha_programada')

    @property
    def citas_todas(self):
        """Retorna todas las citas asociadas a este reclamo, ordenadas por fecha descendente."""
        return self.citas.all().order_by('-fecha_programada')
    """
    Entidad central del sistema.
    Gestiona todo el ciclo de vida de un reclamo desde ingreso hasta resolución.
    """
    id_reclamo = models.AutoField(primary_key=True)
    numero_folio = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(null=True, blank=False)
    resolucion = models.TextField(null=True, blank=True)
    unidad = models.CharField(max_length=50, null=True, blank=True)
    ubicacion_especifica = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        db_column='ubicacion_especifica'
    )
    fecha_ingreso = models.DateTimeField(null=True, blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    tiempo_estimado_horas = models.IntegerField(
        null=True,
        blank=True,
        db_column='tiempo_estimado_horas'
    )
    ESTADO_CHOICES = [
        ('ingresado', 'Ingresado'),
        ('asignado', 'Asignado'),
        ('en_ejecucion', 'En Ejecución'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('resuelto', 'Reclamo Resuelto'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='ingresado')
    prioridad = models.CharField(max_length=20, null=True, blank=True)
    requiere_aprobacion = models.BooleanField(
        default=False,
        db_column='requiere_aprobacion'
    )
    categoria = models.ForeignKey(
        Especialidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reclamos'
    )
    propietario = models.ForeignKey(
        Propietario,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='reclamos'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='reclamos',
        null=False,
        blank=False
    )
    tecnico_asignado = models.ForeignKey(
        'Tecnico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reclamos_asignados'
    )
    requiere_retiro_escombros = models.BooleanField(
        default=False,
        verbose_name='Requiere retiro de escombros'
    )

    class Meta:
        db_table = 'reclamo'
        verbose_name = 'Reclamo'
        verbose_name_plural = 'Reclamos'

    def __str__(self):
        return f"{self.numero_folio} - {self.descripcion[:50] if self.descripcion else 'Sin descripción'}"


# ================================================================
# MODELO 5: USUARIO
# ================================================================
# ================================================================
# MODELO 6: TECNICO
# ================================================================
class Tecnico(models.Model):
    """
    Técnicos especializados.
    Horarios disponibles se almacenan en la tabla Disponibilidad.
    """
    id_tecnico = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tecnico', verbose_name="Usuario del sistema", null=True, blank=True)
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.ForeignKey(
        'Especialidad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tecnicos'
    )
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    zona_cobertura = models.CharField(max_length=100, null=True, blank=True)
    casos_activos = models.IntegerField(null=True, blank=True)
    calificacion_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        db_column='calificacion_promedio'
    )
    estado = models.CharField(max_length=20, null=True, blank=True)
    constructora = models.ForeignKey(
        'Constructora',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tecnicos'
    )

    class Meta:
        db_table = 'tecnico'
        verbose_name = 'Técnico'
        verbose_name_plural = 'Técnicos'

    def __str__(self):
        return self.nombre


# ================================================================
# MODELO 7: ASIGNACIONTECNICO
# ================================================================
class AsignacionTecnico(models.Model):
    """
    Implementa lógica de asignación inteligente con scoring automático.
    """
    id_asignacion = models.AutoField(primary_key=True)
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='asignaciones',
        null=True,
        blank=True
    )
    id_tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        db_column='id_tecnico',
        related_name='asignaciones',
        null=True,
        blank=True
    )
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    metodo_asignacion = models.CharField(max_length=50, null=True, blank=True)
    puntuacion_match = models.IntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'asignacionTecnico'
        verbose_name = 'Asignación Técnico'
        verbose_name_plural = 'Asignaciones Técnicos'

    def __str__(self):
        return f"Asignación {self.id_asignacion}"


# ================================================================
# MODELO 8: CITA
# ================================================================
class Cita(models.Model):
    """
    Agendamiento de visitas técnicas.
    """
    id_cita = models.AutoField(primary_key=True)
    id_tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        db_column='id_tecnico',
        related_name='citas',
        null=True,
        blank=True
    )
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='citas',
        null=True,
        blank=True
    )
    id_cliente = models.ForeignKey(
        'Propietario',
        on_delete=models.CASCADE,
        db_column='id_cliente',
        related_name='citas',
        null=True,
        blank=True
    )
    fecha_programada = models.DateTimeField(null=True, blank=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    estado = models.CharField(max_length=20, null=True, blank=True, choices=ESTADO_CHOICES)
    tipo_cita = models.CharField(max_length=50, null=True, blank=True)
    motivo_reprogramacion = models.TextField(null=True, blank=True)
    recordatorio_enviado = models.BooleanField(default=False)
    duracion_estimada_minutos = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'cita'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'

    def __str__(self):
        return f"Cita {self.id_cita}"


# ================================================================
# MODELO 9: MATERIAL
# ================================================================
class Material(models.Model):
    """
    Materiales disponibles para uso en reclamos.
    """
    id_material = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10, unique=True, default="")
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_column='categoria'
    )
    unidad_medida = models.CharField(max_length=20, null=True, blank=True)
    proveedor = models.CharField(max_length=100, null=True, blank=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actual = models.IntegerField(null=True, blank=True)
    stock_minimo = models.IntegerField(null=True, blank=True)
    ubicacion_bodega = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'material'
        verbose_name = 'Material'
        verbose_name_plural = 'Materiales'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ================================================================
# MODELO 10: USOMATERIAL
# ================================================================
class UsoMaterial(models.Model):
    """
    Registra visitas físicas en las que se usaron materiales para una cita previa asociada.
    """
    id_uso = models.AutoField(primary_key=True)
    id_visita = models.ForeignKey(
        'VisitaTecnica',
        on_delete=models.CASCADE,
        db_column='id_visita',
        related_name='usos_materiales',
        null=True,
        blank=True
    )
    id_material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        db_column='id_material',
        related_name='usos',
        null=True,
        blank=True
    )
    cantidad_usada = models.IntegerField(null=True, blank=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'usoMaterial'
        verbose_name = 'Uso Material'
        verbose_name_plural = 'Usos Materiales'

    def __str__(self):
        return f"Uso {self.id_uso}"


# ================================================================
# MODELO 11: VISITATECNICA
# ================================================================
class VisitaTecnica(models.Model):
    """
    Registra visitas físicas realizadas por técnicos.
    Puede o no estar asociada a una cita previa.
    """
    id_visita = models.AutoField(primary_key=True)
    id_cita = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        db_column='id_cita',
        related_name='visitas_tecnicas',
        null=True,
        blank=True
    )
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='visitas_tecnicas',
        null=True,
        blank=True
    )
    id_tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        db_column='id_tecnico',
        related_name='visitas_tecnicas',
        null=True,
        blank=True
    )
    fecha_visita = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    duracion_real_minutos = models.IntegerField(
        null=True,
        blank=True,
        db_column='duracion_real_minutos'
    )
    tipo_trabajo = models.CharField(max_length=100, null=True, blank=True)
    requiere_seguimiento = models.BooleanField(default=False)
    fecha_proxima_visita = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'visitaTecnica'
        verbose_name = 'Visita Técnica'
        verbose_name_plural = 'Visitas Técnicas'

    def __str__(self):
        return f"Visita {self.id_visita}"


# ================================================================
# MODELO 12: GESTIONESCOMBROS
# ================================================================
class GestionEscombros(models.Model):
    """
    Gestión de retiro de escombros asociados a un reclamo.
    """
    TIPOS_ESCOMBRO = [
        ('construccion', 'Construcción'),
        ('muebles_madera', 'Muebles o madera'),
        ('metales', 'Metales'),
        ('plasticos_carton', 'Plásticos / cartón'),
        ('vidrio', 'Vidrio'),
        ('mixto', 'Mixto'),
        ('otro', 'Otro'),
    ]
    
    id_escombro = models.AutoField(primary_key=True)
    id_visita = models.ForeignKey(
        VisitaTecnica,
        on_delete=models.CASCADE,
        db_column='id_visita',
        related_name='gestion_escombros',
        null=True,
        blank=True
    )
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='gestion_escombros',
        null=True,
        blank=True
    )
    tipo_escombro = models.CharField(
        max_length=20,
        choices=TIPOS_ESCOMBRO,
        null=True,
        blank=True,
        verbose_name='Tipo de escombro'
    )
    volumen_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Volumen estimado (m³)'
    )
    ubicacion_exacta = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ubicación exacta',
        help_text='Punto donde se deberán retirar los escombros'
    )
    fecha_programada_retiro = models.DateField(null=True, blank=True)
    fecha_real_retiro = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('pendiente', 'Pendiente'),
            ('programado', 'Programado'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendiente',
        verbose_name='Estado'
    )
    id_empresa_retiro = models.ForeignKey(
        'EmpresaRetiro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_empresa_retiro',
        related_name='gestiones_escombros',
        verbose_name='Empresa de Retiro'
    )
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'gestionEscombros'
        verbose_name = 'Gestión Escombros'
        verbose_name_plural = 'Gestiones Escombros'

    def __str__(self):
        return f"Escombro {self.id_escombro}"


# ================================================================
# MODELO 12B: ASIGNACIONESCOMBROS
# ================================================================
class AsignacionEscombros(models.Model):
    """
    Asignación de técnicos para el retiro de escombros.
    """
    id_asignacion = models.AutoField(primary_key=True)
    id_escombro = models.ForeignKey(
        GestionEscombros,
        on_delete=models.CASCADE,
        db_column='id_escombro',
        related_name='asignaciones',
        verbose_name='Escombro'
    )
    id_tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        db_column='id_tecnico',
        related_name='asignaciones_escombros',
        verbose_name='Técnico'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('asignado', 'Asignado'),
            ('aceptado', 'Aceptado'),
            ('rechazado', 'Rechazado'),
            ('completado', 'Completado'),
        ],
        default='asignado',
        verbose_name='Estado de Asignación'
    )
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'asignacionEscombros'
        verbose_name = 'Asignación Escombros'
        verbose_name_plural = 'Asignaciones Escombros'
        unique_together = ('id_escombro', 'id_tecnico')

    def __str__(self):
        return f"Asignación {self.id_tecnico} - Escombro {self.id_escombro}"


# ================================================================
# MODELO 13: ENCUESTASATISFACCION
# ================================================================
class EncuestaSatisfaccion(models.Model):
    """
    Encuestas de satisfacción.
    """
    id_encuesta = models.AutoField(primary_key=True)
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='encuestas',
        null=True,
        blank=True
    )
    id_visita = models.ForeignKey(
        VisitaTecnica,
        on_delete=models.CASCADE,
        db_column='id_visita',
        related_name='encuestas',
        null=True,
        blank=True
    )
    puntuacion = models.IntegerField(
        null=True,
        blank=True,
        db_column='puntuacion'
    )
    comentarios = models.TextField(null=True, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    calificacion_tecnico = models.IntegerField(null=True, blank=True)
    calificacion_tiempo = models.IntegerField(
        null=True,
        blank=True,
        db_column='calificacion_tiempo'
    )
    calificacion_solucion = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'encuestaSatisfaccion'
        verbose_name = 'Encuesta Satisfacción'
        verbose_name_plural = 'Encuestas Satisfacción'

    def __str__(self):
        return f"Encuesta {self.id_encuesta}"


# ================================================================
# MODELO 14: NOTIFICACION
# ================================================================
class Notificacion(models.Model):
    """
    Notificaciones del sistema.
    """
    id_notificacion = models.AutoField(primary_key=True)
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='notificaciones',
        null=True,
        blank=True
    )
    tipo = models.CharField(max_length=50, null=True, blank=True)
    mensaje = models.CharField(max_length=200, null=True, blank=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    leido = models.BooleanField(default=False)

    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"Notificación {self.id_notificacion}"


# ================================================================
# MODELO 15: ARCHIVOEVIDENCIA
# ================================================================
class ArchivoEvidencia(models.Model):
    """
    Almacenamiento en AWS S3.
    Se guarda la ruta completa al archivo.
    """
    SUBIDO_POR_CHOICES = [
        ('cliente', 'Cliente'),
        ('tecnico', 'Técnico'),
        ('sistema', 'Sistema'),
    ]
    
    id_archivo = models.AutoField(primary_key=True)
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='archivos_evidencia',
        null=True,
        blank=True
    )
    archivo = models.FileField(
        upload_to=archivo_path, 
        max_length=500, 
        storage=NombreOriginalStorage(),
        null=True, 
        blank=True
    )
    tipo = models.CharField(max_length=50, null=True, blank=True)
    nombre_original = models.CharField(max_length=200, null=True, blank=True)
    tamano_kb = models.IntegerField(
        null=True,
        blank=True,
        db_column='tamano_kb'
    )
    fecha_subida = models.DateTimeField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    subido_por = models.CharField(
        max_length=20,
        choices=SUBIDO_POR_CHOICES,
        default='cliente',
        help_text='Quién subió este archivo'
    )

    class Meta:
        db_table = 'archivoEvidencia'
        verbose_name = 'Archivo Evidencia'
        verbose_name_plural = 'Archivos Evidencias'

    def __str__(self):
        return f"Archivo {self.id_archivo}"


# ================================================================
# MODELO 16: HISTORIAL
# ================================================================
class Historial(models.Model):
    """
    Historial de cambios de estado en reclamos.
    """
    id_historial = models.AutoField(primary_key=True)
    id_reclamo = models.ForeignKey(
        Reclamo,
        on_delete=models.CASCADE,
        db_column='id_reclamo',
        related_name='historial',
        null=True,
        blank=True
    )
    id_usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='historial',
        null=True,
        blank=True
    )
    estado_anterior = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_column='estado_anterior'
    )
    estado_nuevo = models.CharField(max_length=20, null=True, blank=True)
    fecha_cambio = models.DateTimeField(null=True, blank=True)
    motivo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'historial'
        verbose_name = 'Historial'
        verbose_name_plural = 'Historiales'

    def __str__(self):
        return f"Historial {self.id_historial}"


# ================================================================
# MODELO 17: DISPONIBILIDAD
# ================================================================
class Disponibilidad(models.Model):
    """
    Disponibilidad horaria de un técnico.
    Permite dos tipos:
    1. Recurrente (es_recurrente=True): Se repite cada semana en el mismo día
    2. Puntual (es_recurrente=False): Es solo para una fecha específica
    """
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    id_disponibilidad = models.AutoField(primary_key=True)
    id_tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        db_column='id_tecnico',
        related_name='disponibilidades'
    )
    fecha = models.DateField(
        db_column='fecha',
        help_text='Fecha del día para el cual se especifica disponibilidad'
    )
    hora_inicio = models.TimeField(
        db_column='hora_inicio',
        help_text='Hora de inicio de disponibilidad (HH:MM)'
    )
    hora_fin = models.TimeField(
        db_column='hora_fin',
        help_text='Hora de fin de disponibilidad (HH:MM)'
    )
    es_recurrente = models.BooleanField(
        db_column='es_recurrente',
        default=False,
        help_text='Si es True, este horario se repite cada semana en el mismo día'
    )
    dia_semana = models.IntegerField(
        db_column='dia_semana',
        choices=DIAS_SEMANA,
        null=True,
        blank=True,
        help_text='Día de la semana para horarios recurrentes (0=Lunes, 6=Domingo)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at'
    )

    class Meta:
        db_table = 'disponibilidad'
        verbose_name = 'Disponibilidad'
        verbose_name_plural = 'Disponibilidades'
        ordering = ['fecha', 'hora_inicio']
        unique_together = [['id_tecnico', 'fecha', 'hora_inicio', 'hora_fin']]

    def __str__(self):
        tipo = "Recurrente" if self.es_recurrente else "Puntual"
        return f"Disponibilidad {self.id_tecnico} - {tipo} - {self.fecha} {self.hora_inicio}:{self.hora_fin}"
    
    def get_dia_semana_display_custom(self):
        """Retorna el nombre del día de la semana"""
        if self.dia_semana is not None:
            return dict(self.DIAS_SEMANA).get(self.dia_semana, 'Desconocido')
        return 'N/A'


# ================================================================
# MODELO: EMPRESAS DE RETIRO DE ESCOMBROS
# ================================================================
class EmpresaRetiro(models.Model):
    """
    Empresas contratadas para retiro de escombros.
    """
    id_empresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre de Empresa')
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    activa = models.BooleanField(default=True, verbose_name='¿Activa?')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'empresaRetiro'
        verbose_name = 'Empresa de Retiro'
        verbose_name_plural = 'Empresas de Retiro'
    
    def __str__(self):
        return self.nombre


# ================================================================
# MODELO: ENCUESTA DE SATISFACCIÓN - VERSIÓN ACTUAL EN USO
# (Vea la clase anterior en línea 690 para la definición activa)
# ================================================================

