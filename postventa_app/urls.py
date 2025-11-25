from django.urls import path
from . import views

urlpatterns = [
    # Página de inicio ahora es login
    path('', views.login_view, name='login'),

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard Cliente
    path('mis-reclamos/', views.mis_reclamos, name='mis_reclamos'),
    
    # Dashboard Técnico
    path('tecnico/dashboard/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('tecnico/dashboard/', views.dashboard_tecnico, name='tecnico_dashboard'),  # alias
    path('tecnico/disponibilidad/', views.disponibilidad_tecnico, name='disponibilidad_tecnico'),
    path('api/disponibilidad/crear/', views.crear_disponibilidad, name='crear_disponibilidad'),
    path('api/disponibilidad/<int:disponibilidad_id>/eliminar/', views.eliminar_disponibilidad, name='eliminar_disponibilidad'),
    path('api/disponibilidad/eliminar-json/', views.eliminar_disponibilidad_json, name='eliminar_disponibilidad_json'),
    path('tecnico/citas/', views.tecnico_historial_citas, name='tecnico_historial_citas'),
    path('tecnico/reclamo/<int:reclamo_id>/', views.tecnico_detalle_reclamo, name='tecnico_detalle_reclamo'),
    path('tecnico/reclamo/<int:reclamo_id>/cita/<int:cita_id>/', views.tecnico_detalle_reclamo, name='tecnico_detalle_reclamo_cita'),
    path('tecnico/cita/<int:cita_id>/', views.tecnico_detalle_cita, name='tecnico_detalle_cita'),
    path('tecnico/cita/<int:cita_id>/iniciar/', views.tecnico_iniciar_cita, name='tecnico_iniciar_cita'),
    path('tecnico/cita/<int:cita_id>/completar/', views.tecnico_completar_cita, name='tecnico_completar_cita'),

    # Gestión de Escombros
    path('tecnico/escombros/', views.tecnico_historial_escombros, name='tecnico_historial_escombros'),
    path('tecnico/escombro/<int:escombro_id>/actualizar/', views.tecnico_actualizar_escombro, name='tecnico_actualizar_escombro'),

    # Reclamos
    path('reclamo/crear/', views.crear_reclamo, name='crear_reclamo'),
    path('reclamo/<int:reclamo_id>/', views.detalle_reclamo, name='detalle_reclamo'),
    path('cita/<int:cita_id>/', views.cliente_detalle_cita, name='cliente_detalle_cita'),

    # Utilidades
    path('test/', views.test_view, name='test'),
    path('health/', views.check_health, name='check_health'),

    # API
    path('api/tecnicos/', views.tecnicos_en_tiempo_real, name='tecnicos_en_tiempo_real'),

    # Gestión de citas
    path('cita/<int:cita_id>/reagendar/', views.reagendar_cita, name='reagendar_cita'),
    path('cita/<int:cita_id>/agendar-nueva/', views.agendar_nueva_cita_tecnico, name='agendar_nueva_cita_tecnico'),
    path('cita/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('reclamo/<int:reclamo_id>/cancelar/', views.cancelar_reclamo, name='cancelar_reclamo'),

    # Alias para compatibilidad con código antiguo
    path('historial/', views.mis_reclamos, name='historial_reclamos'),

    # Dashboard Supervisor
    path('supervisor/dashboard/', views.dashboard_supervisor, name='dashboard_supervisor'),
    path('supervisor/kpis/', views.dashboard_kpis, name='dashboard_kpis'),
    path('supervisor/reclamos/', views.supervisor_reclamos, name='supervisor_reclamos'),
    path('supervisor/reclamo/<int:reclamo_id>/', views.supervisor_detalle_reclamo, name='supervisor_detalle_reclamo'),
    
    # Validación de Retiro de Escombros Supervisor
    path('supervisor/escombros/', views.supervisor_validar_escombros, name='supervisor_validar_escombros'),
    path('supervisor/escombro/<int:escombro_id>/procesar/', views.supervisor_procesar_escombro, name='supervisor_procesar_escombro'),
    
    # Evidencia Fotográfica Supervisor
    path('supervisor/evidencia/', views.supervisor_evidencia_fotografica, name='supervisor_evidencia_fotografica'),
    path('supervisor/reclamo/<int:reclamo_id>/evidencia/', views.supervisor_detalle_evidencia, name='supervisor_detalle_evidencia'),
    
    # Control de Materiales Supervisor
    path('supervisor/materiales/', views.supervisor_control_materiales, name='supervisor_control_materiales'),
    path('supervisor/visita/<int:visita_id>/materiales/', views.supervisor_detalle_materiales_visita, name='supervisor_detalle_materiales_visita'),
    
    # Disponibilidad de Técnicos Supervisor
    path('supervisor/disponibilidad/', views.supervisor_disponibilidad_tecnicos, name='supervisor_disponibilidad_tecnicos'),
    path('supervisor/disponibilidad/calendario/', views.supervisor_calendario_disponibilidad, name='supervisor_calendario_disponibilidad'),
    
    # APIs para Power BI - KPIs
    path('api/kpis/export/', views.api_kpis_export, name='api_kpis_export'),
    path('api/kpis/export-csv/', views.export_kpis_csv, name='export_kpis_csv'),
    path('api/kpis/public/', views.api_kpis_export_public, name='api_kpis_public'),  # SIN autenticación para Power BI
    
    # Dashboard Administrador
    path('administrador/', views.dashboard_admin, name='dashboard_admin'),
    path('administrador-reclamos/', views.admin_reclamos, name='admin_reclamos'),
    path('administrador-reclamo/<int:reclamo_id>/', views.admin_detalle_reclamo, name='admin_detalle_reclamo'),
    path('administrador-usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('administrador-crear-supervisor/', views.admin_crear_supervisor, name='admin_crear_supervisor'),
    path('administrador-eliminar-supervisor/<int:supervisor_id>/', views.admin_eliminar_supervisor, name='admin_eliminar_supervisor'),
    path('administrador-tecnicos/', views.admin_tecnicos, name='admin_tecnicos'),
    path('administrador-crear-tecnico/', views.admin_crear_tecnico, name='admin_crear_tecnico'),
    path('administrador-editar-tecnico/<int:tecnico_id>/', views.admin_editar_tecnico, name='admin_editar_tecnico'),
    path('administrador-eliminar-tecnico/<int:tecnico_id>/', views.admin_eliminar_tecnico, name='admin_eliminar_tecnico'),
    path('administrador-reportes/', views.admin_reportes, name='admin_reportes'),
    path('administrador-costos/', views.admin_costos, name='admin_costos'),

    # Elimino la URL dashboard-propietario porque no existe la vista
]
