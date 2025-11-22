from django.contrib import admin
from .models import (
    Constructora, Proyecto, Tecnico, Reclamo,
    AsignacionTecnico, Cita, Material, UsoMaterial, VisitaTecnica,
    GestionEscombros, AsignacionEscombros, EncuestaSatisfaccion, Notificacion, ArchivoEvidencia, Historial, Especialidad, Propietario, Unidad, Perfil, Disponibilidad, EmpresaRetiro
)
# ========================================
# ADMIN: ESPECIALIDAD
# ========================================
@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


# ========================================
# ADMIN: PROPIETARIO
# ========================================
class UnidadInline(admin.TabularInline):
    model = Unidad
    extra = 0
    fields = ['nombre', 'proyecto', 'descripcion']
    readonly_fields = ['proyecto']
    can_delete = False


@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'tipo_propietario', 'email', 'telefono', 'proyecto']
    search_fields = ['nombre', 'rut', 'email']
    list_filter = ['tipo_propietario', 'proyecto']
    ordering = ['nombre']
    readonly_fields = []
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'rut', 'tipo_propietario', 'email', 'telefono', 'direccion')
        }),
        ('Asociaciones', {
            'fields': ('user', 'proyecto')
        }),
            # ('Otras Datos', {
            #     'fields': ('fecha_compra', 'notas_internas')
            # }),
    )
    inlines = [UnidadInline]


# ========================================
# ADMIN: CONSTRUCTORA
# ========================================
@admin.register(Constructora)
class ConstructoraAdmin(admin.ModelAdmin):
    list_display = ['razon_social', 'rut', 'email_contacto', 'telefono', 'estado']
    search_fields = ['razon_social', 'rut', 'nombre_fantasia']
    list_filter = ['estado', 'fecha_registro']
    ordering = ['razon_social']


# ========================================
# ADMIN: PROYECTO
# ========================================
@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'constructora', 'cantidad_unidades', 'estado', 'fecha_entrega']
    search_fields = ['nombre', 'direccion']
    list_filter = ['estado', 'tipo_proyecto', 'fecha_entrega']
    ordering = ['-fecha_entrega']



# ========================================
# ADMIN: TECNICO
# ========================================
@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'especialidad', 'constructora', 'email', 'telefono', 'estado', 'calificacion_promedio']
    search_fields = ['nombre', 'rut', 'email', 'especialidad__nombre']
    list_filter = ['estado', 'especialidad']
    ordering = ['nombre']


# ========================================
# ADMIN: RECLAMO
# ========================================
@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ['numero_folio', 'get_categoria_nombre', 'estado', 'prioridad', 'fecha_ingreso', 'resolucion']
    search_fields = ['numero_folio', 'descripcion', 'resolucion']
    list_filter = ['estado', 'prioridad', 'categoria', 'fecha_ingreso']
    ordering = ['-fecha_ingreso']
    readonly_fields = ['numero_folio', 'get_categoria_nombre']
    fieldsets = (
        ('Datos principales', {
            'fields': (
                'numero_folio', 'descripcion', 'resolucion', 'categoria',
                'propietario', 'proyecto', 'unidad', 'ubicacion_especifica',
                'tecnico_asignado',
                'estado', 'prioridad', 'fecha_ingreso'
            )
        }),
    )
    def get_categoria_nombre(self, obj):
        """Muestra el nombre de la especialidad en lugar del ID"""
        if obj.categoria:
            # La categoria ahora es una instancia de Especialidad (después de migración)
            if isinstance(obj.categoria, Especialidad):
                return obj.categoria.nombre
            else:
                # Fallback para compatibilidad con datos antiguos
                try:
                    especialidad = Especialidad.objects.get(id=int(obj.categoria))
                    return especialidad.nombre
                except (Especialidad.DoesNotExist, ValueError, TypeError):
                    return str(obj.categoria)
        return "No especificada"
    get_categoria_nombre.short_description = 'Categoría'
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'estado':
            from django import forms
            kwargs['widget'] = forms.Select(choices=[
                ('', '---------'),
                ('pendiente', 'Pendiente'),
                ('asignado', 'Asignado'),
                ('en_proceso', 'En Proceso'),
                ('resuelto', 'Resuelto'),
                ('cerrado', 'Cerrado'),
                ('cancelado', 'Cancelado'),
            ])
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# ========================================
# ADMIN: ASIGNACION TECNICO
# ========================================
@admin.register(AsignacionTecnico)
class AsignacionTecnicoAdmin(admin.ModelAdmin):
    list_display = ['id_asignacion', 'id_reclamo', 'id_tecnico', 'fecha_asignacion', 'metodo_asignacion', 'estado'
]
    search_fields = ['id_reclamo__numero_folio', 'id_tecnico__nombre']
    list_filter = ['estado', 'metodo_asignacion', 'fecha_asignacion']
    ordering = ['-fecha_asignacion']


# ========================================
# ADMIN: CITA
# ========================================
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['id_cita', 'id_reclamo', 'id_tecnico', 'fecha_programada', 'estado', 'tipo_cita']
    search_fields = ['id_reclamo__numero_folio', 'id_tecnico__nombre']
    list_filter = ['estado', 'tipo_cita', 'fecha_programada']
    ordering = ['-fecha_programada']
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'estado':
            from django import forms
            kwargs['widget'] = forms.Select(choices=[
                ('', '---------'),
                ('pendiente', 'Pendiente'),
                ('confirmada', 'Confirmada'),
                ('realizada', 'Realizada'),
                ('cancelada', 'Cancelada'),
                ('reprogramada', 'Reprogramada'),
            ])
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# ========================================
# ADMIN: MATERIAL
# ========================================
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'costo_unitario']
    search_fields = ['codigo', 'nombre', 'proveedor']
    list_filter = ['categoria']
    ordering = ['codigo']


# ========================================
# ADMIN: USO MATERIAL
# ========================================
@admin.register(UsoMaterial)
class UsoMaterialAdmin(admin.ModelAdmin):
    list_display = ['id_uso', 'id_visita', 'id_material', 'cantidad_usada', 'fecha_uso']
    search_fields = ['id_material__nombre']
    list_filter = ['fecha_uso']
    ordering = ['-fecha_uso']


# ========================================
# ADMIN: VISITA TECNICA
# ========================================
@admin.register(VisitaTecnica)
class VisitaTecnicaAdmin(admin.ModelAdmin):
    list_display = ['id_visita', 'id_reclamo', 'id_tecnico', 'fecha_visita', 'estado', 'duracion_real_minutos']
    search_fields = ['id_reclamo__numero_folio', 'id_tecnico__nombre']
    list_filter = ['estado', 'fecha_visita', 'requiere_seguimiento']
    ordering = ['-fecha_visita']


# ========================================
# ADMIN: GESTION ESCOMBROS
# ========================================
@admin.register(GestionEscombros)
class GestionEscombrosAdmin(admin.ModelAdmin):
    list_display = ['id_escombro', 'id_reclamo', 'tipo_escombro', 'volumen_m3', 'estado', 'fecha_programada_retiro', 'id_empresa_retiro']
    search_fields = ['id_reclamo__numero_folio', 'tipo_escombro', 'id_empresa_retiro__nombre']
    list_filter = ['estado', 'fecha_programada_retiro', 'fecha_real_retiro']
    ordering = ['-fecha_programada_retiro']
    fieldsets = (
        ('Información Básica', {
            'fields': ('id_reclamo', 'id_visita', 'tipo_escombro', 'volumen_m3')
        }),
        ('Programación', {
            'fields': ('fecha_programada_retiro', 'fecha_real_retiro', 'estado')
        }),
        ('Empresa y Costos', {
            'fields': ('id_empresa_retiro', 'costo')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id_escombro',)


@admin.register(AsignacionEscombros)
class AsignacionEscombrosAdmin(admin.ModelAdmin):
    list_display = ['id_asignacion', 'id_escombro', 'id_tecnico', 'fecha_asignacion', 'estado']
    search_fields = ['id_tecnico__nombre', 'id_escombro__id_escombro', 'id_escombro__id_reclamo__numero_folio']
    list_filter = ['estado', 'fecha_asignacion']
    ordering = ['-fecha_asignacion']
    fieldsets = (
        ('Asignación', {
            'fields': ('id_escombro', 'id_tecnico', 'fecha_asignacion')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id_asignacion', 'fecha_asignacion')


# ========================================
# ADMIN: ENCUESTA SATISFACCION
# ========================================
@admin.register(EncuestaSatisfaccion)
class EncuestaSatisfaccionAdmin(admin.ModelAdmin):
    list_display = ['id_encuesta', 'id_reclamo', 'puntuacion', 'fecha_respuesta']
    search_fields = ['id_reclamo__numero_folio', 'comentarios']
    list_filter = ['puntuacion', 'fecha_respuesta']
    ordering = ['-fecha_respuesta']
    fieldsets = (
        ('Información General', {
            'fields': ('id_reclamo', 'id_visita', 'puntuacion')
        }),
        ('Calificaciones', {
            'fields': ('calificacion_tecnico', 'calificacion_tiempo', 'calificacion_solucion')
        }),
        ('Comentarios y Fechas', {
            'fields': ('comentarios', 'fecha_respuesta')
        }),
    )


# ========================================
# ADMIN: NOTIFICACION
# ========================================
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['id_notificacion', 'tipo', 'mensaje', 'fecha_envio', 'leido']
    search_fields = ['mensaje', 'tipo']
    list_filter = ['tipo', 'leido', 'fecha_envio']
    ordering = ['-fecha_envio']


# ========================================
# ADMIN: ARCHIVO EVIDENCIA
# ========================================
@admin.register(ArchivoEvidencia)
class ArchivoEvidenciaAdmin(admin.ModelAdmin):
    list_display = ['id_archivo', 'id_reclamo', 'tipo', 'nombre_original', 'tamano_kb', 'fecha_subida']
    search_fields = ['nombre_original', 'id_reclamo__numero_folio']
    list_filter = ['tipo', 'fecha_subida']
    ordering = ['-fecha_subida']


# ========================================
# ADMIN: HISTORIAL
# ========================================
@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ['id_historial', 'id_reclamo', 'id_usuario', 'estado_anterior', 'estado_nuevo', 'fecha_cambio']
    search_fields = ['id_reclamo__numero_folio', 'id_usuario__nombre']
    list_filter = ['estado_anterior', 'estado_nuevo', 'fecha_cambio']
    ordering = ['-fecha_cambio']


# ========================================
# ADMIN: PERFIL
# ========================================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rol', 'telefono', 'direccion')

# ========================================
# ADMIN: DISPONIBILIDAD
# ========================================
@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ['id_tecnico', 'fecha', 'hora_inicio', 'hora_fin', 'es_recurrente', 'dia_semana', 'created_at']
    list_filter = ['id_tecnico', 'fecha', 'es_recurrente', 'dia_semana']
    search_fields = ['id_tecnico__nombre']
    fieldsets = (
        ('Técnico', {'fields': ('id_tecnico',)}),
        ('Horario', {'fields': ('fecha', 'hora_inicio', 'hora_fin')}),
        ('Recurrencia', {'fields': ('es_recurrente', 'dia_semana')}),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmpresaRetiro)
class EmpresaRetiroAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'email', 'activa']
    search_fields = ['nombre', 'email']
    list_filter = ['activa', 'fecha_creacion']
    fieldsets = (
        ('Información de la Empresa', {
            'fields': ('nombre', 'telefono', 'email', 'direccion')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
    )
    readonly_fields = ('id_empresa', 'fecha_creacion')




