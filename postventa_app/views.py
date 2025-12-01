from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Q, Prefetch, Avg, Sum, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta, date
import calendar
from .models import Reclamo, ArchivoEvidencia, Propietario, Tecnico, Proyecto, Cita, AsignacionTecnico, Especialidad, VisitaTecnica, Disponibilidad, EncuestaSatisfaccion, GestionEscombros, AsignacionEscombros, UsoMaterial, EmpresaRetiro, Perfil
from .forms import ReclamoForm, RegistroClienteForm, CitaForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET
from .kpi_calculator import KPICalculator
import json
import csv


def get_cliente_from_user(user):
    """
    Intenta resolver el Propietario asociado a un objeto auth.User.
    
    Estrategia:
    - Intentar buscar por email
    - Si no, intentar buscar por RUT coincidente con username
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    try:
        return Propietario.objects.get(email__iexact=(user.email or ''))
    except Propietario.DoesNotExist:
        pass

    # Intentar por username como RUT
    try:
        return Propietario.objects.get(rut=user.username)
    except Propietario.DoesNotExist:
        return None


# ========================================
# VISTAS PÚBLICAS
# ========================================

def registro(request):
    """Registro de nuevos clientes"""
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido.')
            return redirect('mis_reclamos')
    else:
        form = RegistroClienteForm()
    return render(request, 'postventa_app/registro.html', {'form': form})



def login_view(request):
    """Login de usuarios"""
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir al dashboard correcto según su rol
        if request.user.is_staff:
            return redirect('dashboard_admin')
        
        supervisor = get_supervisor_from_user(request.user)
        if supervisor:
            return redirect('dashboard_supervisor')
        
        tecnico = get_tecnico_from_user(request.user)
        if tecnico:
            return redirect('dashboard_tecnico')
        
        # Si es cliente/propietario
        return redirect('mis_reclamos')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirigir según tipo de usuario
            if user.is_staff:
                return redirect('dashboard_admin')
            
            # Si es supervisor, redirigir a dashboard_supervisor
            supervisor = get_supervisor_from_user(user)
            if supervisor:
                return redirect('dashboard_supervisor')
            
            # Si es técnico, redirigir a dashboard_tecnico
            tecnico = get_tecnico_from_user(user)
            if tecnico:
                return redirect('dashboard_tecnico')
            return redirect('mis_reclamos')
        else:
            # Mostrar errores de autenticación más claros
            messages.error(request, 'Usuario o contraseña incorrectos. Verifica tus credenciales.')
    else:
        form = AuthenticationForm()
    return render(request, 'cliente_propietario/login.html', {'form': form})


def logout_view(request):
    """Logout de usuarios"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# ========================================
# DASHBOARD CLIENTE
# ========================================

@login_required
def dashboard_cliente(request):
    """Dashboard principal del cliente"""
    cliente = get_cliente_from_user(request.user)
    
    if not cliente:
        messages.error(request, 'No se encontró información de cliente.')
        return redirect('mis_reclamos')
    
    # Obtener reclamos del cliente
    reclamos = Reclamo.objects.filter(id_cliente=cliente).order_by('-fecha_ingreso')
    
    # Estadísticas
    total_reclamos = reclamos.count()
    reclamos_pendientes = reclamos.filter(estado='pendiente').count()
    reclamos_en_proceso = reclamos.filter(estado__in=['asignado', 'en_proceso']).count()
    reclamos_resueltos = reclamos.filter(estado='resuelto').count()
    
    context = {
        'cliente': cliente,
        'reclamos': reclamos[:10],  # Últimos 10
        'total_reclamos': total_reclamos,
        'reclamos_pendientes': reclamos_pendientes,
        'reclamos_en_proceso': reclamos_en_proceso,
        'reclamos_resueltos': reclamos_resueltos,
    }
    
    return render(request, 'cliente_propietario/dashboard_cliente.html', context)


@login_required
def crear_reclamo(request):
    """Crear un nuevo reclamo"""
    cliente = get_cliente_from_user(request.user)
    
    if not cliente:
        messages.error(request, 'Debe estar registrado como cliente.')
        return redirect('mis_reclamos')
    
    from .forms import ImagenReclamoFormSet
    if request.method == 'POST':
        form = ReclamoForm(request.POST, cliente=cliente)
        formset = ImagenReclamoFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            reclamo = form.save(commit=False)
            reclamo.propietario = cliente
            reclamo.proyecto = form.cleaned_data.get('proyecto')
            reclamo.fecha_ingreso = timezone.now()
            reclamo.estado = 'pendiente'
            
            # Generar folio único
            year = timezone.now().year
            folio_generado = False
            max_intentos = 10
            intentos = 0
            
            while not folio_generado and intentos < max_intentos:
                # Obtener el último número de folio del año
                ultimo_reclamo = Reclamo.objects.filter(
                    numero_folio__startswith=f'PV-{year}'
                ).order_by('-numero_folio').first()
                
                if ultimo_reclamo:
                    # Extraer el número del último folio
                    try:
                        ultimo_numero = int(ultimo_reclamo.numero_folio.split('-')[-1])
                        nuevo_numero = ultimo_numero + 1
                    except (ValueError, IndexError):
                        nuevo_numero = 1
                else:
                    nuevo_numero = 1
                
                reclamo.numero_folio = f'PV-{year}-{str(nuevo_numero).zfill(4)}'
                
                try:
                    reclamo.save()
                    folio_generado = True
                except Exception as e:
                    if 'UNIQUE constraint failed' in str(e):
                        intentos += 1
                        continue
                    else:
                        raise
            
            if not folio_generado:
                messages.error(request, 'No se pudo generar un folio único. Intente nuevamente.')
                return redirect('crear_reclamo')
            
            # Capturar técnico seleccionado y crear asignación
            tecnico_id = request.POST.get('tecnico_id')
            fecha_cita = request.POST.get('fecha_cita')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')
            mensaje_cita = ''
            
            if tecnico_id:
                try:
                    tecnico = Tecnico.objects.get(id_tecnico=tecnico_id)
                    reclamo.tecnico_asignado = tecnico
                    reclamo.estado = 'asignado'
                    reclamo.save()
                    AsignacionTecnico.objects.create(
                        id_reclamo=reclamo,
                        id_tecnico=tecnico,
                        fecha_asignacion=timezone.now(),
                        metodo_asignacion='manual',
                        estado='activa'
                    )
                    
                    # Crear la cita si se seleccionaron fecha y hora
                    if fecha_cita and hora_inicio:
                        # Combinar fecha y hora
                        from datetime import datetime
                        fecha_hora_str = f"{fecha_cita} {hora_inicio}"
                        fecha_programada = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
                        
                        # Convertir fecha para mostrar en mensaje (DD/MM/YYYY)
                        fecha_formateada = datetime.strptime(fecha_cita, '%Y-%m-%d').strftime('%d/%m/%Y')
                        
                        Cita.objects.create(
                            id_reclamo=reclamo,
                            id_tecnico=tecnico,
                            id_cliente=cliente,
                            fecha_programada=fecha_programada,
                            estado='pendiente',
                            tipo_cita='visita_tecnica',
                            duracion_estimada_minutos=120  # 2 horas por defecto
                        )
                        mensaje_cita = f' y cita agendada para el {fecha_formateada} a las {hora_inicio}'
                        
                except Tecnico.DoesNotExist:
                    pass
            
            # Guardar evidencias
            formset.instance = reclamo
            formset.save()
            # Marcar todas las evidencias como subidas por cliente
            reclamo.archivos_evidencia.all().update(subido_por='cliente')
            messages.success(request, f'Reclamo {reclamo.numero_folio} creado exitosamente{mensaje_cita}.')
            return redirect('mis_reclamos')
        else:
            # Mostrar errores del formulario
            import json
            print("=== FORM ERRORS ===")
            print(f"Form errors: {form.errors}")
            print(f"Formset errors: {formset.errors}")
            print(f"Form data: {request.POST}")
            print("==================")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for idx, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(request, f'Archivo {idx}: {field}: {error}')
    else:
        initial_data = {}
        if hasattr(cliente, 'id_proyecto') and cliente.id_proyecto:
            initial_data['id_proyecto'] = cliente.id_proyecto.id_proyecto
        form = ReclamoForm(initial=initial_data, cliente=cliente)
        formset = ImagenReclamoFormSet()
    return render(request, 'cliente_propietario/crear_reclamo.html', {
        'form': form,
        'formset': formset,
        'cliente': cliente,
        'propietario': cliente  # Compatibility alias for template
    })


@login_required
def detalle_reclamo(request, reclamo_id):
    """Ver detalle de un reclamo"""
    cliente = get_cliente_from_user(request.user)
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    # Verificar que el reclamo pertenece al cliente (o es admin)
    if not request.user.is_staff and reclamo.propietario != cliente:
        messages.error(request, 'No tiene permiso para ver este reclamo.')
        return redirect('dashboard_cliente')
    
    # Obtener archivos subidos por el cliente
    archivos_cliente = list(ArchivoEvidencia.objects.filter(
        id_reclamo=reclamo,
        subido_por='cliente'
    ))
    
    # Obtener archivos subidos por el técnico (siempre, para reclamos resueltos)
    archivos_tecnico = list(ArchivoEvidencia.objects.filter(
        id_reclamo=reclamo,
        subido_por='tecnico'
    ))
    
    citas = Cita.objects.filter(id_reclamo=reclamo).order_by('-fecha_programada')
    
    # Verificar si hay alguna cita completada
    hay_cita_completada = citas.filter(estado='completada').exists()
    
    # Calcular número de cita completada para mostrar en resolución
    citas_completadas = list(citas.filter(estado='completada').order_by('fecha_programada'))
    numero_cita_completada = None
    # Solo mostrar número de visita si hay más de una cita completada
    if len(citas_completadas) > 1:
        numero_cita_completada = len(citas_completadas)
    
    # Obtener técnico asignado
    asignacion = AsignacionTecnico.objects.filter(id_reclamo=reclamo, estado='activa').first()
    tecnico_asignado = asignacion.id_tecnico if asignacion else None
    
    # Calcular iniciales del técnico
    tecnico_iniciales = ''
    if tecnico_asignado and tecnico_asignado.nombre:
        partes = tecnico_asignado.nombre.strip().split()
        tecnico_iniciales = ''.join([p[0].upper() for p in partes if p])
    
    # Obtener nombre de la categoría (especialidad) si existe
    categoria_nombre = None
    if reclamo.categoria:
        # La categoria ahora es una instancia de Especialidad (después de migración)
        if isinstance(reclamo.categoria, Especialidad):
            categoria_nombre = reclamo.categoria.nombre
        else:
            # Fallback para compatibilidad con datos antiguos
            try:
                especialidad = Especialidad.objects.get(id=int(reclamo.categoria))
                categoria_nombre = especialidad.nombre
            except (Especialidad.DoesNotExist, ValueError, TypeError):
                categoria_nombre = str(reclamo.categoria)
    
    # Determinar cita accionable y en curso
    from datetime import date
    hoy = date.today()
    cita_hoy_accionable = None
    cita_en_curso = None
    cita_para_visita = None
    for cita in citas:
        if cita.estado in ['pendiente', 'confirmada'] and cita.fecha_programada.date() == hoy:
            cita_hoy_accionable = cita
        if cita.estado == 'en_curso':
            cita_en_curso = cita
        if cita.estado == 'completada':
            cita_para_visita = cita
    
    # Obtener visita técnica si existe (del reclamo resuelto)
    visita_detalle = None
    if cita_para_visita:
        try:
            visita_detalle = VisitaTecnica.objects.get(id_cita=cita_para_visita)
        except VisitaTecnica.DoesNotExist:
            pass
    
    context = {
        'reclamo': reclamo,
        'cliente': cliente,
        'archivos_cliente': archivos_cliente,
        'archivos_tecnico': archivos_tecnico,
        'citas': citas,
        'tecnico_asignado': tecnico_asignado,
        'tecnico_iniciales': tecnico_iniciales,
        'categoria_nombre': categoria_nombre,
        'visita_detalle': visita_detalle,
        'hay_cita_completada': hay_cita_completada,
        'numero_cita_completada': numero_cita_completada,
    }
    context.update({
        'cita_hoy_accionable': cita_hoy_accionable,
        'cita_en_curso': cita_en_curso,
    })
    return render(request, 'cliente_propietario/detalle_reclamo.html', context)


@login_required
def cliente_detalle_cita(request, cita_id):
    """Detalle de cita para cliente - ver información de la cita completada"""
    from datetime import date
    
    cita = get_object_or_404(Cita, id_cita=cita_id)
    cliente = get_cliente_from_user(request.user)
    
    # Verificar que la cita pertenece al cliente
    if not cliente or cita.id_cliente != cliente:
        messages.error(request, 'No tienes permiso para acceder a esta cita.')
        return redirect('mis_reclamos')
    
    reclamo = cita.id_reclamo
    if not reclamo:
        messages.error(request, 'Esta cita no tiene un reclamo asociado.')
        return redirect('mis_reclamos')
    
    # Obtener archivos separados por quien los subió
    archivos = ArchivoEvidencia.objects.filter(id_reclamo=reclamo)
    archivos_cliente = archivos.filter(subido_por='cliente')
    archivos_tecnico = archivos.filter(subido_por='tecnico')
    
    # Obtener todas las citas del reclamo
    citas = Cita.objects.filter(id_reclamo=reclamo).order_by('-fecha_programada')
    
    # Calcular número de visita completada (para mostrar en resolución)
    citas_completadas = list(citas.filter(estado='completada').order_by('fecha_programada'))
    numero_visita_completada = None
    # Solo mostrar número de visita si hay más de una cita completada
    if len(citas_completadas) > 1 and cita in citas_completadas:
        # Encontrar la posición de la cita actual en la lista de completadas
        numero_visita_completada = citas_completadas.index(cita) + 1
    
    # Obtener visita técnica si existe
    visita_detalle = None
    try:
        visita_detalle = VisitaTecnica.objects.get(id_cita=cita)
    except VisitaTecnica.DoesNotExist:
        pass
    
    # Obtener nombre de la categoría (especialidad) si existe
    categoria_nombre = None
    if reclamo.categoria:
        if isinstance(reclamo.categoria, Especialidad):
            categoria_nombre = reclamo.categoria.nombre
        else:
            try:
                especialidad = Especialidad.objects.get(id=int(reclamo.categoria))
                categoria_nombre = especialidad.nombre
            except (Especialidad.DoesNotExist, ValueError):
                categoria_nombre = str(reclamo.categoria)
    
    context = {
        'reclamo': reclamo,
        'cliente': cliente,
        'cita': cita,
        'visita_detalle': visita_detalle,
        'archivos': archivos,
        'archivos_cliente': archivos_cliente,
        'archivos_tecnico': archivos_tecnico,
        'citas': citas,
        'categoria_nombre': categoria_nombre,
        'today': date.today(),
        'numero_visita_completada': numero_visita_completada,
    }
    return render(request, 'cliente_propietario/detalle_cita.html', context)


@login_required
def mis_reclamos(request):
    """Lista de todos los reclamos del cliente"""
    cliente = get_cliente_from_user(request.user)
    
    if not cliente:
        return HttpResponse('No se encontró información de cliente asociada a tu usuario. Por favor, contacta soporte.', status=403)
    
    # Filtros
    estado = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')
    
    reclamos = Reclamo.objects.filter(propietario=cliente).select_related('proyecto', 'propietario').prefetch_related(
        'asignaciones__id_tecnico',
        Prefetch('citas', queryset=Cita.objects.filter(estado__in=['pendiente', 'confirmada', 'en_curso']).order_by('-id_cita'), to_attr='citas_activas'),
        Prefetch('citas', queryset=Cita.objects.all().order_by('-id_cita'), to_attr='citas_todas')
    )
    
    if estado:
        reclamos = reclamos.filter(estado=estado)
    
    if busqueda:
        reclamos = reclamos.filter(
            Q(numero_folio__icontains=busqueda) |
            Q(titulo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    reclamos = reclamos.order_by('-fecha_ingreso')
    
    # Agregar técnico asignado a cada reclamo
    for reclamo in reclamos:
        asignacion_activa = reclamo.asignaciones.filter(estado='activa').first()
        reclamo.tecnico_asignado = asignacion_activa.id_tecnico if asignacion_activa else None
        
        # Obtener nombre de la categoría (especialidad)
        if reclamo.categoria:
            # categoria ahora es una instancia de Especialidad
            if isinstance(reclamo.categoria, Especialidad):
                reclamo.categoria_nombre = reclamo.categoria.nombre
            else:
                # Por si acaso todavía hay IDs en la BD
                try:
                    especialidad = Especialidad.objects.get(id=int(reclamo.categoria))
                    reclamo.categoria_nombre = especialidad.nombre
                except (Especialidad.DoesNotExist, ValueError):
                    reclamo.categoria_nombre = str(reclamo.categoria)
        else:
            reclamo.categoria_nombre = "Sin categoría"
    
    # Estadísticas
    total_reclamos = reclamos.count()
    pendientes = reclamos.filter(estado='pendiente').count()
    en_proceso = reclamos.filter(estado__in=['asignado', 'en_proceso']).count()
    resueltos = reclamos.filter(estado='resuelto').count()
    
    context = {
        'cliente': cliente,
        'propietario': cliente,  # Alias para compatibilidad con template
        'reclamos': reclamos,
        'estado_filtro': estado,
        'busqueda': busqueda,
        'total_reclamos': total_reclamos,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'resueltos': resueltos,
    }
    
    return render(request, 'cliente_propietario/mis_reclamos.html', context)


@login_required
def mis_citas(request):
    """Lista de citas del cliente"""
    cliente = get_cliente_from_user(request.user)
    
    if not cliente:
        messages.error(request, 'No se encontró información de cliente.')
        return redirect('mis_reclamos')
    
    citas = Cita.objects.filter(id_cliente=cliente).order_by('-fecha_programada')
    
    context = {
        'cliente': cliente,
        'citas': citas,
    }
    
    return render(request, 'cliente_propietario/mis_citas.html', context)


# ========================================
# VISTAS AUXILIARES / API
# ========================================

def test_view(request):
    """Vista de prueba"""
    return HttpResponse("Sistema de Postventa - OK")


@require_http_methods(["GET"])
def check_health(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })


@require_GET
def tecnicos_en_tiempo_real(request):
    """Devuelve la lista de técnicos activos en tiempo real filtrados por categoría o por ID específico (JSON)."""
    categoria_id = request.GET.get('categoria_id')
    especialidad_id = request.GET.get('especialidad_id')  # Para compatibilidad
    proyecto_id = request.GET.get('proyecto_id')
    tecnico_id = request.GET.get('tecnico_id')
    excluir_cita_id = request.GET.get('excluir_cita_id')  # ID de cita a excluir (para reagendamiento)
    
    # Usar categoria_id si está disponible, sino usar especialidad_id
    filter_id = categoria_id or especialidad_id
    
    # print AJAX debug eliminado
    
    # Obtener el cliente del usuario autenticado
    cliente = None
    if request.user.is_authenticated:
        cliente = get_cliente_from_user(request.user)
    # print AJAX debug eliminado
    
    # Filtrar técnicos activos
    tecnicos = Tecnico.objects.filter(estado='activo')
    
    # Si se especifica un técnico específico, filtrar solo por ese
    if tecnico_id:
        tecnicos = tecnicos.filter(id_tecnico=tecnico_id)
    # print AJAX debug eliminado
    else:
        pass
    
    # Filtrar por especialidad/categoría
    if filter_id:
        tecnicos = tecnicos.filter(especialidad_id=filter_id)
    # print AJAX debug eliminado
    
    # Filtrar por constructora del proyecto del cliente
    if proyecto_id:
        try:
            proyecto = Proyecto.objects.get(id_proyecto=proyecto_id)
            # print AJAX debug eliminado
            if proyecto.constructora:
                tecnicos = tecnicos.filter(constructora=proyecto.constructora)
                # print AJAX debug eliminado
        except Proyecto.DoesNotExist:
            # print AJAX debug eliminado
            pass
    elif cliente and hasattr(cliente, 'proyecto') and cliente.proyecto:
        # Si no hay proyecto_id en params, usar el del cliente
        proyecto = cliente.proyecto
        if proyecto.constructora:
            tecnicos = tecnicos.filter(constructora=proyecto.constructora)
    
    data = []
    for t in tecnicos:
        # Obtener iniciales del nombre
        nombre_partes = t.nombre.split()
        iniciales = ''.join([p[0].upper() for p in nombre_partes[:2]])
        
        # Obtener disponibilidad semanal y próximos horarios desde la BD
        disponibilidad_semanal = []
        proximos_horarios = []
        
        # Obtener citas ya agendadas del técnico para filtrarlas
        citas_query = Cita.objects.filter(
            id_tecnico=t,
            estado__in=['pendiente', 'confirmada']
        )
        
        for c in citas_query:
            pass
        
        # Si estamos reagendando, excluir la cita actual
        if excluir_cita_id:
            pass
            citas_query = citas_query.exclude(id_cita=excluir_cita_id)
        
        citas_ocupadas = citas_query.values_list('fecha_programada', flat=True)
        
        # Convertir a set de strings "YYYY-MM-DD HH:MM" para comparación rápida
        # IMPORTANTE: Convertir de UTC a hora local de Chile antes de formatear
        horarios_ocupados = set()
        for cita_fecha in citas_ocupadas:
            if cita_fecha:
                # Convertir de UTC a zona horaria local (America/Santiago)
                cita_fecha_local = timezone.localtime(cita_fecha)
                fecha_str = cita_fecha_local.strftime('%Y-%m-%d %H:%M')
                horarios_ocupados.add(fecha_str)
        
        
        # Obtener horarios del técnico desde la tabla Disponibilidad
        hoy = datetime.now().date()
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        # Obtener disponibilidades RECURRENTES del técnico
        disponibilidades_recurrentes = Disponibilidad.objects.filter(
            id_tecnico=t,
            es_recurrente=True
        ).order_by('dia_semana', 'hora_inicio')
        
        if disponibilidades_recurrentes.exists():
            # Generar proyección de 14 días (2 semanas) desde los horarios recurrentes
            for i in range(1, 15):  # Desde mañana hasta dentro de 14 días
                fecha_actual = hoy + timedelta(days=i)
                dia_semana_num = fecha_actual.weekday()
                
                # Buscar horarios recurrentes para este día de la semana
                for disp in disponibilidades_recurrentes:
                    if disp.dia_semana == dia_semana_num:
                        hora_inicio_str = str(disp.hora_inicio)[:5]  # HH:MM
                        hora_fin_str = str(disp.hora_fin)[:5]  # HH:MM
                        horario_completo = f"{fecha_actual.strftime('%Y-%m-%d')} {hora_inicio_str}"
                        
                        # Solo agregar si no está ocupado
                        if horario_completo not in horarios_ocupados:
                            proximos_horarios.append({
                                'fecha': fecha_actual.strftime('%Y-%m-%d'),
                                'fecha_formateada': fecha_actual.strftime('%d/%m'),
                                'dia_nombre': dias_semana[dia_semana_num],
                                'hora_inicio': hora_inicio_str,
                                'hora_fin': hora_fin_str
                            })
            
            # Agregar disponibilidades semanales desde horarios recurrentes únicos
            disponibilidades_unicas = {}
            for disp in disponibilidades_recurrentes:
                dia_nombre = dias_semana[disp.dia_semana]
                if dia_nombre not in disponibilidades_unicas:
                    disponibilidades_unicas[dia_nombre] = []
                
                horario_str = f"{str(disp.hora_inicio)[:5]} - {str(disp.hora_fin)[:5]}"
                if horario_str not in disponibilidades_unicas[dia_nombre]:
                    disponibilidades_unicas[dia_nombre].append(horario_str)
            
            for dia_nombre in dias_semana[:5]:  # Solo lunes a viernes
                if dia_nombre in disponibilidades_unicas:
                    disponibilidad_semanal.append({
                        'dia': dia_nombre,
                        'horarios': [{'hora_inicio': h.split(' - ')[0], 'hora_fin': h.split(' - ')[1]} 
                                      for h in disponibilidades_unicas[dia_nombre]]
                    })
        else:
            # Fallback: horarios por defecto si no tiene horarios recurrentes configurados
            for i in range(1, 15):  # Próximos 14 días (desde mañana)
                fecha = hoy + timedelta(days=i)
                dia_semana_num = fecha.weekday()
                
                # Solo lunes a viernes
                if dia_semana_num < 5:
                    horarios_default = [
                        {'hora_inicio': '09:00', 'hora_fin': '13:00'},
                        {'hora_inicio': '14:00', 'hora_fin': '18:00'}
                    ]
                    
                    for horario in horarios_default:
                        # Verificar si este horario está ocupado
                        hora_inicio_str = horario['hora_inicio']
                        horario_completo = f"{fecha.strftime('%Y-%m-%d')} {hora_inicio_str}"
                        
                        # Solo agregar si no está ocupado
                        if horario_completo not in horarios_ocupados:
                            proximos_horarios.append({
                                'fecha': fecha.strftime('%Y-%m-%d'),
                                'fecha_formateada': fecha.strftime('%d/%m'),
                                'dia_nombre': dias_semana[dia_semana_num],
                                'hora_inicio': horario['hora_inicio'],
                                'hora_fin': horario['hora_fin']
                            })
            
            # Disponibilidad semanal por defecto
            for dia in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']:
                disponibilidad_semanal.append({
                    'dia': dia,
                    'horarios': [
                        {'hora_inicio': '09:00', 'hora_fin': '13:00'},
                        {'hora_inicio': '14:00', 'hora_fin': '18:00'}
                    ]
                })
        
        tecnico_data = {
            'id': t.id_tecnico,
            'nombre': t.nombre,
            'email': t.email,
            'especialidad': t.especialidad.nombre if t.especialidad else '',
            'constructora': t.constructora.razon_social if t.constructora else 'Sin constructora',
            'calificacion': float(t.calificacion_promedio) if t.calificacion_promedio else 4.5,
            'casos_activos': t.casos_activos or 0,
            'iniciales': iniciales,
            'foto_url': None,  # Agregar URL de foto si existe en el modelo
            'tiene_disponibilidad': len(proximos_horarios) > 0,
            'proximos_horarios': proximos_horarios,
            'disponibilidad_semanal': disponibilidad_semanal
        }
        data.append(tecnico_data)
    
    return JsonResponse({'tecnicos': data})


# ========================================
# GESTIÓN DE CITAS
# ========================================

@login_required
@require_http_methods(["POST"])
def reagendar_cita(request, cita_id):
    """Reagendar una cita existente (para cliente)"""
    cita = get_object_or_404(Cita, id_cita=cita_id)
    cliente = get_cliente_from_user(request.user)
    
    # Si no es cliente, intentar como técnico
    if not cliente:
        tecnico = get_tecnico_from_user(request.user)
        if not tecnico or cita.id_tecnico != tecnico:
            messages.error(request, 'No tienes permiso para modificar esta cita.')
            return redirect('dashboard_tecnico' if tecnico else 'mis_reclamos')
    else:
        # Verificar que la cita pertenece al cliente
        if cita.id_cliente.id != cliente.id:
            messages.error(request, 'No tienes permiso para modificar esta cita.')
            return redirect('mis_reclamos')
    
    # Validar que la cita no esté en curso
    if cita.estado == 'en_curso':
        messages.error(request, 'No puedes reagendar una cita que está en curso. Completa la visita primero.')
        if cliente:
            return redirect('mis_reclamos')
        else:
            return redirect('tecnico_detalle_reclamo', reclamo_id=cita.id_reclamo.id_reclamo)
    
    # Obtener el nuevo horario del formulario (formato: "YYYY-MM-DD|HH:MM:SS")
    slot = request.POST.get('slot', '')
    if not slot or '|' not in slot:
        messages.error(request, 'Por favor selecciona un horario válido.')
        if cliente:
            return redirect('mis_reclamos')
        else:
            return redirect('tecnico_detalle_reclamo', reclamo_id=cita.id_reclamo.id_reclamo)
    
    try:
        fecha_str, hora_str = slot.split('|')
        
        # Intentar con formato HH:MM:SS, si falla intentar con HH:MM
        try:
            nueva_fecha = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M:%S')
        except ValueError:
            nueva_fecha = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        
        # Convertir a timezone-aware
        nueva_fecha = timezone.make_aware(nueva_fecha)
        
        # Validar que el horario no esté ocupado (excluyendo esta misma cita)
        cita_conflicto = Cita.objects.filter(
            id_tecnico=cita.id_tecnico,
            fecha_programada=nueva_fecha,
            estado__in=['pendiente', 'confirmada']
        ).exclude(id_cita=cita.id_cita).first()
        
        if cita_conflicto:
            messages.error(request, f'El horario seleccionado ya está ocupado. Por favor selecciona otro horario.')
            if cliente:
                return redirect('mis_reclamos')
            else:
                return redirect('tecnico_detalle_reclamo', reclamo_id=cita.id_reclamo.id_reclamo)
        
        # CREAR UNA NUEVA CITA en lugar de modificar la actual
        # Eliminar la cita antigua (ya que será reemplazada por la nueva)
        cita.delete()
        
        # Crear la nueva cita con estado pendiente
        nueva_cita = Cita.objects.create(
            id_reclamo=cita.id_reclamo,
            id_cliente=cita.id_cliente,
            id_tecnico=cita.id_tecnico,
            fecha_programada=nueva_fecha,
            estado='pendiente'
        )
        
        # Notificar arriba, no finalizar visita
        messages.success(request, f'Cita reagendada exitosamente para el {nueva_fecha.strftime("%d/%m/%Y a las %H:%M")}.')
    except Exception as e:
        messages.error(request, f'Error al reagendar la cita: {str(e)}')
    
    # Si es solicitud AJAX (desde técnico), retornar JSON y no redirigir
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Cita reagendada exitosamente'})
    
    # Si es cliente, redirigir a mis_reclamos
    if cliente:
        return redirect('mis_reclamos')
    else:
        # Si es técnico y no es AJAX, también redirigir
        return redirect('tecnico_detalle_reclamo', reclamo_id=cita.id_reclamo.id_reclamo)


@login_required
@require_http_methods(["POST"])
def agendar_nueva_cita_tecnico(request, cita_id):
    """Crear una nueva cita sin eliminar la actual (para técnico con cita en_curso)"""
    cita_actual = get_object_or_404(Cita, id_cita=cita_id)
    tecnico = get_tecnico_from_user(request.user)
    
    if not tecnico or cita_actual.id_tecnico != tecnico:
        messages.error(request, 'No tienes permiso para crear una nueva cita.')
        return redirect('dashboard_tecnico')
    
    # Obtener el nuevo horario del formulario (formato: "YYYY-MM-DD|HH:MM:SS")
    slot = request.POST.get('slot', '')
    if not slot or '|' not in slot:
        messages.error(request, 'Por favor selecciona un horario válido.')
        return redirect('tecnico_detalle_reclamo', reclamo_id=cita_actual.id_reclamo.id_reclamo)
    
    try:
        fecha_str, hora_str = slot.split('|')
        
        # Intentar con formato HH:MM:SS, si falla intentar con HH:MM
        try:
            nueva_fecha = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M:%S')
        except ValueError:
            nueva_fecha = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        
        # Convertir a timezone-aware
        nueva_fecha = timezone.make_aware(nueva_fecha)
        
        # Validar que el horario no esté ocupado
        cita_conflicto = Cita.objects.filter(
            id_tecnico=tecnico,
            fecha_programada=nueva_fecha,
            estado__in=['pendiente', 'confirmada', 'en_curso']
        ).exclude(id_cita=cita_actual.id_cita).first()
        
        if cita_conflicto:
            messages.error(request, f'El horario seleccionado ya está ocupado. Por favor selecciona otro horario.')
            return redirect('tecnico_detalle_reclamo', reclamo_id=cita_actual.id_reclamo.id_reclamo)
        
        # CREAR UNA NUEVA CITA sin tocar la actual
        nueva_cita = Cita.objects.create(
            id_reclamo=cita_actual.id_reclamo,
            id_cliente=cita_actual.id_cliente,
            id_tecnico=tecnico,
            fecha_programada=nueva_fecha,
            estado='pendiente'
        )
        
        messages.success(request, f'Nueva cita agendada exitosamente para el {nueva_fecha.strftime("%d/%m/%Y a las %H:%M")}.')
    except Exception as e:
        messages.error(request, f'Error al agendar la nueva cita: {str(e)}')
    
    # Si es solicitud AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Nueva cita agendada exitosamente'})
    
    return redirect('tecnico_detalle_reclamo', reclamo_id=cita_actual.id_reclamo.id_reclamo)


@login_required
@require_http_methods(["POST"])
def cancelar_cita(request, cita_id):
    """Cancelar una cita existente"""
    cita = get_object_or_404(Cita, id_cita=cita_id)
    cliente = get_cliente_from_user(request.user)
    
    # Verificar que la cita pertenece al cliente
    if not cliente or cita.propietario.id != cliente.id:
        messages.error(request, 'No tienes permiso para cancelar esta cita.')
        return redirect('mis_reclamos')
    
    # Cancelar la cita
        cita.estado = 'cancelada'
        cita.save()
        # Liberar el horario en la tabla Disponibilidad si existe una cita asociada
        tecnico = cita.id_tecnico
        fecha = cita.fecha_programada
        if tecnico and fecha:
            # El sistema no necesita liberar explícitamente porque la cita se cancela
            # pero el horario permanece disponible en la tabla Disponibilidad
            pass
    
    messages.success(request, 'Cita cancelada exitosamente.')
    return redirect('mis_reclamos')


@login_required
@require_http_methods(["POST"])
def cancelar_reclamo(request, reclamo_id):
    """Cancelar un reclamo existente"""
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    cliente = get_cliente_from_user(request.user)
    
    # Verificar que el reclamo pertenece al cliente
    if not cliente or reclamo.propietario.id != cliente.id:
        messages.error(request, 'No tienes permiso para cancelar este reclamo.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No tienes permiso'}, status=403)
        return redirect('mis_reclamos')
    
    # Verificar que el reclamo no esté en estado final
    if reclamo.estado in ['resuelto', 'cerrado', 'cancelado']:
        messages.error(request, 'No puedes cancelar un reclamo que ya está finalizado.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Reclamo ya finalizado'}, status=400)
        return redirect('mis_reclamos')
    
    # Cancelar el reclamo y sus citas activas
    reclamo.estado = 'cancelado'
    reclamo.save()
    
    # Cancelar citas activas asociadas
    Cita.objects.filter(
        id_reclamo=reclamo,
        estado__in=['pendiente', 'confirmada']
    ).update(estado='cancelada')
    
    messages.success(request, f'Reclamo {reclamo.numero_folio} cancelado exitosamente.')
    
    # Si es una petición AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Reclamo {reclamo.numero_folio} cancelado exitosamente.'})
    
    return redirect('mis_reclamos')


# ========================================
# DASHBOARD TÉCNICO
# ========================================

def get_tecnico_from_user(user):
    """
    Intenta resolver el Técnico asociado a un objeto auth.User.
    Estrategia:
    - Buscar por email (case-insensitive)
    - Buscar por rut (username)
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return Tecnico.objects.get(email__iexact=(user.email or ''))
    except Tecnico.DoesNotExist:
        pass
    try:
        return Tecnico.objects.get(rut=user.username)
    except Tecnico.DoesNotExist:
        return None

@login_required
def tecnico_detalle_reclamo(request, reclamo_id, cita_id=None):
    """Ver detalle de un reclamo desde la perspectiva del técnico"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    
    # Verificar que el reclamo está asignado a este técnico
    asignacion = AsignacionTecnico.objects.filter(id_tecnico=tecnico, id_reclamo=reclamo).first()
    if not asignacion and not request.user.is_staff:
        messages.error(request, 'No tiene permiso para ver este reclamo.')
        return redirect('dashboard_tecnico')
    
    # Obtener archivos y citas relacionadas
    archivos = ArchivoEvidencia.objects.filter(id_reclamo=reclamo)
    archivos_cliente = archivos.filter(subido_por='cliente')
    archivos_tecnico = archivos.filter(subido_por='tecnico')
    citas = Cita.objects.filter(id_reclamo=reclamo, id_tecnico=tecnico).order_by('-fecha_programada')
    
    # Calcular número de cita completada para mostrar en resolución
    citas_completadas = list(citas.filter(estado='completada').order_by('fecha_programada'))
    numero_cita_completada = None
    # Solo mostrar número de visita si hay más de una cita completada
    if len(citas_completadas) > 1:
        numero_cita_completada = len(citas_completadas)
    
    # Obtener la cita específica si se pasa cita_id
    cita_detalle = None
    if cita_id:
        cita_detalle = get_object_or_404(Cita, id_cita=cita_id, id_reclamo=reclamo, id_tecnico=tecnico)
    
    # Obtener nombre de la categoría (especialidad) si existe
    categoria_nombre = None
    if reclamo.categoria:
        # Check if it's already an Especialidad object
        if isinstance(reclamo.categoria, Especialidad):
            categoria_nombre = reclamo.categoria.nombre
        else:
            # Try to convert from ID
            try:
                especialidad = Especialidad.objects.get(id=int(reclamo.categoria))
                categoria_nombre = especialidad.nombre
            except (Especialidad.DoesNotExist, ValueError):
                categoria_nombre = str(reclamo.categoria)
    
    # Calcular iniciales del técnico
    tecnico_iniciales = ''
    if tecnico and tecnico.nombre:
        partes = tecnico.nombre.strip().split()
        tecnico_iniciales = ''.join([p[0].upper() for p in partes if p])

    # Determinar cita accionable y en curso
    from datetime import date
    hoy = date.today()
    cita_hoy_accionable = None
    cita_mas_reciente = cita_detalle if cita_detalle else (citas.first() if citas else None)
    cita_en_curso = None
    
    # Si se pasó una cita_id y está en_curso, usarla como cita_en_curso
    if cita_detalle and cita_detalle.estado == 'en_curso':
        cita_en_curso = cita_detalle
    
    # Si no hay cita_en_curso especificada, buscar en todas las citas
    if not cita_en_curso:
        for cita in citas:
            cita_fecha = cita.fecha_programada.date() if cita.fecha_programada else None
            if cita_fecha == hoy and cita.estado in ['pendiente', 'confirmada']:
                cita_hoy_accionable = cita
            if cita.estado == 'en_curso':
                cita_en_curso = cita

    # Obtener materiales disponibles para el formulario dinámico
    from .models import Material, VisitaTecnica, UsoMaterial
    materiales_disponibles = Material.objects.all().order_by('nombre')
    
    # Si hay una visita en curso, obtener los materiales ya utilizados
    materiales_usados = []
    visita_en_curso = None
    if cita_en_curso:
        visita_en_curso = VisitaTecnica.objects.filter(id_cita=cita_en_curso).first()
        if visita_en_curso:
            materiales_usados = UsoMaterial.objects.filter(id_visita=visita_en_curso).select_related('id_material')
    
    # Obtener la visita de la cita seleccionada (si está completada)
    visita_detalle = None
    archivos_visita = []
    if cita_detalle and cita_detalle.estado == 'completada':
        visita_detalle = VisitaTecnica.objects.filter(id_cita=cita_detalle).first()
    
    # Mostrar siempre los archivos subidos por el técnico en el apartado "Imágenes de la Visita"
    archivos_visita = list(archivos_tecnico)

    context = {
        'reclamo': reclamo,
        'tecnico': tecnico,
        'tecnico_iniciales': tecnico_iniciales,
        'archivos': archivos,
        'archivos_cliente': list(archivos_cliente),
        'archivos_tecnico': list(archivos_tecnico),
        'archivos_visita': archivos_visita,
        'citas': citas,
        'categoria_nombre': categoria_nombre,
        'cita_hoy_accionable': cita_hoy_accionable,
        'cita_mas_reciente': cita_mas_reciente,
        'cita_en_curso': cita_en_curso,
        'visita_en_curso': visita_en_curso,
        'visita_detalle': visita_detalle,
        'materiales_disponibles': materiales_disponibles,
        'materiales_usados': materiales_usados,
        'numero_cita_completada': numero_cita_completada,
    }
    return render(request, 'tecnico/detalle_reclamo.html', context)


@login_required
def tecnico_detalle_cita(request, cita_id):
    """Detalle de cita para técnico - permite iniciar/cerrar visita, agregar comentarios y resolución"""
    from datetime import date
    
    cita = get_object_or_404(Cita, id_cita=cita_id)
    tecnico = get_tecnico_from_user(request.user)
    
    # Verificar que la cita pertenece al técnico
    if not tecnico or cita.id_tecnico.id_tecnico != tecnico.id_tecnico:
        messages.error(request, 'No tienes permiso para acceder a esta cita.')
        return redirect('dashboard_tecnico')
    
    reclamo = cita.id_reclamo
    if not reclamo:
        messages.error(request, 'Esta cita no tiene un reclamo asociado.')
        return redirect('dashboard_tecnico')
    
    # Procesar formulario de comentarios/resolución si es POST
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '').strip()
        resolucion = request.POST.get('resolucion', '').strip()
        accion = request.POST.get('accion', '')
        
        if accion == 'iniciar':
            # Iniciar la visita
            if cita.estado != 'en_curso':
                cita.estado = 'en_curso'
                cita.save()
                messages.success(request, 'Visita iniciada.')
        
        elif accion == 'cerrar':
            # Cerrar la visita con comentarios y resolución
            if comentario or resolucion:
                cita.estado = 'completada'
                cita.save()
                
                # Actualizar el reclamo con la resolución
                if resolucion:
                    reclamo.descripcion = f"{reclamo.descripcion}\n\n--- Resolución del técnico {tecnico.nombre} ---\n{resolucion}"
                    reclamo.estado = 'completado'
                    reclamo.save()
                
                messages.success(request, 'Visita cerrada y reclamo marcado como completado.')
            else:
                messages.error(request, 'Por favor ingresa un comentario o resolución.')
    
    # Obtener archivos y citas relacionadas
    archivos = ArchivoEvidencia.objects.filter(id_reclamo=reclamo)
    citas = Cita.objects.filter(id_reclamo=reclamo, id_tecnico=tecnico).order_by('-fecha_programada')
    
    # Obtener nombre de la categoría (especialidad) si existe
    categoria_nombre = None
    if reclamo.categoria:
        if isinstance(reclamo.categoria, Especialidad):
            categoria_nombre = reclamo.categoria.nombre
        else:
            try:
                especialidad = Especialidad.objects.get(id=int(reclamo.categoria))
                categoria_nombre = especialidad.nombre
            except (Especialidad.DoesNotExist, ValueError):
                categoria_nombre = str(reclamo.categoria)
    
    context = {
        'reclamo': reclamo,
        'tecnico': tecnico,
        'cita': cita,
        'archivos': archivos,
        'citas': citas,
        'categoria_nombre': categoria_nombre,
        'today': date.today(),
    }
    return render(request, 'tecnico/detalle_cita.html', context)


@login_required
def tecnico_historial_citas(request):
    """Historial de citas del técnico"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    # Filtro por estado
    estado = request.GET.get('estado', 'todas')
    
    # Búsqueda por nombre del propietario o número de reclamo
    busqueda = request.GET.get('busqueda', '').strip()
    
    citas = Cita.objects.filter(id_tecnico=tecnico).select_related(
        'id_reclamo',
        'id_cliente',
        'id_reclamo__proyecto'
    ).order_by('-fecha_programada')
    
    if estado != 'todas' and estado:
        citas = citas.filter(estado=estado)
    
    if busqueda:
        citas = citas.filter(
            Q(id_cliente__nombre__icontains=busqueda) |
            Q(id_reclamo__numero_folio__icontains=busqueda)
        )
    
    context = {
        'tecnico': tecnico,
        'citas': citas,
        'estado': estado,
        'busqueda': busqueda,
    }
    
    return render(request, 'tecnico/historial_citas.html', context)


@login_required
def dashboard_tecnico(request):
    """Dashboard principal del técnico"""
    from datetime import date
    
    tecnico = get_tecnico_from_user(request.user)
    perfil = None
    if hasattr(request.user, 'perfil'):
        perfil = request.user.perfil
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('mis_reclamos')

    # KPIs: cantidad de citas, pendientes, resueltas, etc.
    total_citas = Cita.objects.filter(id_tecnico=tecnico).count()
    citas_pendientes = Cita.objects.filter(id_tecnico=tecnico, estado='pendiente').count()
    citas_completadas = Cita.objects.filter(id_tecnico=tecnico, estado='completada').count()
    citas_proximas_count = Cita.objects.filter(id_tecnico=tecnico, estado__in=['pendiente', 'confirmada']).count()

    kpi_cards = [
        ("Total Citas", "primary", total_citas),
        ("Pendientes", "warning", citas_pendientes),
        ("Completadas", "success", citas_completadas),
        ("Próximas", "secondary", citas_proximas_count),
    ]

    # Obtener próximas citas para mostrar en la tabla
    proximas_citas_raw = Cita.objects.filter(
        id_tecnico=tecnico,
        estado__in=['pendiente', 'confirmada', 'en_curso']
    ).select_related(
        'id_reclamo',
        'id_cliente',
        'id_reclamo__proyecto'
    ).order_by('fecha_programada')
    
    # Filtrar en Python para excluir citas con reclamo None o con id_reclamo vacío
    proximas_citas = [
        c for c in proximas_citas_raw 
        if c.id_reclamo and c.id_reclamo.id_reclamo
    ][:10]
    
    # Contar solo citas de hoy
    today = date.today()
    citas_hoy = [
        c for c in proximas_citas 
        if c.fecha_programada.date() == today
    ]

    context = {
        'tecnico': tecnico,
        'perfil': perfil,
        'kpi_cards': kpi_cards,
        'proximas_citas': proximas_citas,
        'citas_hoy': citas_hoy,
        'today': today,
    }
    return render(request, 'tecnico/dashboard.html', context)


@login_required
def disponibilidad_tecnico(request):
    """Gestión de disponibilidad horaria semanal del técnico"""
    from datetime import date, timedelta
    import json
    
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    # Obtener semana actual o la especificada
    semana_offset = int(request.GET.get('semana', 0))
    hoy = date.today()
    
    # Obtener el lunes de la semana actual
    # Si hoy es lunes (0), el lunes es hoy
    # Si hoy es domingo (6), el lunes es mañana
    if hoy.weekday() == 6:  # Si es domingo
        lunes = hoy + timedelta(days=1)  # El lunes es mañana
    else:
        dias_hasta_lunes = hoy.weekday()
        lunes = hoy - timedelta(days=dias_hasta_lunes)
    
    # Aplicar el offset de semana
    lunes = lunes + timedelta(weeks=semana_offset)
    domingo = lunes + timedelta(days=6)
    
    # Crear lista de días de la semana
    dias_semana = []
    for i in range(5):  # Solo lunes a viernes (0-4)
        dia = lunes + timedelta(days=i)
        dias_semana.append({
            'fecha': dia,
            'nombre': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'][i],
        })
    
    # Obtener disponibilidades RECURRENTES del técnico
    disponibilidades_recurrentes = Disponibilidad.objects.filter(
        id_tecnico=tecnico,
        es_recurrente=True
    ).order_by('dia_semana', 'hora_inicio')
    
    # Generar horarios para los próximos 14 días (2 semanas)
    disponibilidad_por_dia = {}
    for i in range(14):  # 14 días = 2 semanas
        fecha_actual = lunes + timedelta(days=i)
        dia_semana_num = fecha_actual.weekday()
        
        # Buscar horarios recurrentes para este día de la semana
        for disp in disponibilidades_recurrentes:
            if disp.dia_semana == dia_semana_num:
                dia_key = fecha_actual.isoformat()
                if dia_key not in disponibilidad_por_dia:
                    disponibilidad_por_dia[dia_key] = []
                disponibilidad_por_dia[dia_key].append({
                    'id': disp.id_disponibilidad,
                    'hora_inicio': str(disp.hora_inicio),
                    'hora_fin': str(disp.hora_fin),
                })
    
    # Añadir disponibilidades a los días de esta semana
    for dia in dias_semana:
        dia_key = dia['fecha'].isoformat()
        dia['disponibilidades'] = disponibilidad_por_dia.get(dia_key, [])
    
    # Obtener semana anterior y siguiente
    semana_anterior = semana_offset - 1
    semana_siguiente = semana_offset + 1
    
    context = {
        'tecnico': tecnico,
        'dias_semana': dias_semana,
        'lunes': lunes,
        'domingo': domingo,
        'semana_offset': semana_offset,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
        'today': hoy,
    }
    return render(request, 'tecnico/disponibilidad.html', context)


@login_required
def crear_disponibilidad(request):
    """AJAX: Crear nueva disponibilidad horaria recurrente"""
    from datetime import datetime, time
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        return JsonResponse({'error': 'No autenticado'}, status=403)
    
    try:
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        
        # Validar datos
        if not fecha or not hora_inicio or not hora_fin:
            return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)
        
        # Asegurar que el horario esté en formato HH:MM (sin segundos)
        if len(hora_inicio) == 5:  # Si es HH:MM
            hora_inicio = hora_inicio + ":00"
        if len(hora_fin) == 5:
            hora_fin = hora_fin + ":00"
        
        # Parsear la fecha para obtener el día de la semana
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        dia_semana = fecha_obj.weekday()  # 0=Lunes, 6=Domingo
        
        # Crear disponibilidad como RECURRENTE
        disp = Disponibilidad.objects.create(
            id_tecnico=tecnico,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            es_recurrente=True,  # Marcar como recurrente
            dia_semana=dia_semana  # Asignar el día de la semana
        )
        
        # Retornar sin segundos
        return JsonResponse({
            'success': True,
            'id': disp.id_disponibilidad,
            'hora_inicio': str(disp.hora_inicio)[:5],  # HH:MM
            'hora_fin': str(disp.hora_fin)[:5],        # HH:MM
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def eliminar_disponibilidad(request, disponibilidad_id):
    """AJAX: Eliminar disponibilidad horaria"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        return JsonResponse({'error': 'No autenticado'}, status=403)
    
    try:
        disp = Disponibilidad.objects.get(id_disponibilidad=disponibilidad_id, id_tecnico=tecnico)
        disp.delete()
        return JsonResponse({'success': True})
    except Disponibilidad.DoesNotExist:
        return JsonResponse({'error': 'No encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def eliminar_disponibilidad_json(request):
    """AJAX: Eliminar disponibilidad de la tabla Disponibilidad"""
    from datetime import datetime
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        return JsonResponse({'error': 'No autenticado'}, status=403)
    
    try:
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        
        if not fecha or not hora_inicio or not hora_fin:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)
        
        # Convertir fecha string a date object
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        # Buscar y eliminar la disponibilidad de la tabla
        disponibilidad = Disponibilidad.objects.filter(
            id_tecnico=tecnico,
            fecha=fecha_obj,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        ).first()
        
        if disponibilidad:
            disponibilidad.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Disponibilidad no encontrada'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@login_required
@require_http_methods(["POST"])
def tecnico_iniciar_cita(request, cita_id):
    """Iniciar una cita (cambiar estado a en_curso)"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    cita = get_object_or_404(Cita, id_cita=cita_id)
    
    # Verificar que la cita pertenece a este técnico
    if cita.id_tecnico != tecnico and not request.user.is_staff:
        messages.error(request, 'No tiene permiso para iniciar esta cita.')
        return redirect('dashboard_tecnico')
    
    # Cambiar estado a en_curso
    cita.estado = 'en_curso'
    cita.save()
    
    # Crear la visita técnica asociada
    from .models import VisitaTecnica
    VisitaTecnica.objects.get_or_create(
        id_cita=cita,
        defaults={
            'id_reclamo': cita.id_reclamo,
            'id_tecnico': tecnico,
            'fecha_visita': timezone.now(),
            'estado': 'en_curso',
        }
    )
    
    # Usar numero_folio en vez de folio
    messages.success(request, f'Cita iniciada - Reclamo {cita.id_reclamo.numero_folio}     ')
    return redirect('tecnico_detalle_reclamo_cita', reclamo_id=cita.id_reclamo.id_reclamo, cita_id=cita_id)


@login_required
@require_http_methods(["POST"])
def tecnico_completar_cita(request, cita_id):
    """Completar una cita en curso"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    cita = get_object_or_404(Cita, id_cita=cita_id)
    
    # Verificar que la cita pertenece a este técnico
    if cita.id_tecnico != tecnico and not request.user.is_staff:
        messages.error(request, 'No tiene permiso para completar esta cita.')
        return redirect('dashboard_tecnico')
    
    # Procesar materiales usados
    from .models import VisitaTecnica, UsoMaterial, Material, GestionEscombros
    # Crear o buscar la visita técnica asociada a la cita
    visita, _ = VisitaTecnica.objects.get_or_create(id_cita=cita, defaults={
        'id_reclamo': cita.id_reclamo,
        'id_tecnico': tecnico,
        'fecha_visita': timezone.now(),
        'estado': 'completada',
    })
    # Nuevo formato: recorrer todos los materiales disponibles
    materiales = Material.objects.all()
    for material in materiales:
        check_name = f"material_usado_{material.id_material}"
        cantidad_name = f"material_cantidad_{material.id_material}"
        usado = request.POST.get(check_name)
        cantidad = request.POST.get(cantidad_name)
        if usado and cantidad:
            try:
                UsoMaterial.objects.create(
                    id_visita=visita,
                    id_material=material,
                    cantidad_usada=int(cantidad),
                    fecha_uso=timezone.now(),
                )
            except Exception:
                continue
    
    # Procesar escombros si aplica
    requiere_escombro = request.POST.get('requiere_escombro')
    if requiere_escombro:
        tipo_escombro = request.POST.get('tipo_escombro', '').strip()
        volumen_escombro = request.POST.get('volumen_escombro', 0)
        ubicacion_escombro = request.POST.get('ubicacion_escombro', '').strip()
        observaciones_escombro = request.POST.get('observaciones_escombro', '').strip()
        
        try:
            GestionEscombros.objects.create(
                id_visita=visita,
                id_reclamo=cita.id_reclamo,
                tipo_escombro=tipo_escombro or 'otro',
                volumen_m3=float(volumen_escombro) if volumen_escombro else 0,
                ubicacion_exacta=ubicacion_escombro,
                estado='pendiente',
                observaciones=observaciones_escombro,
            )
            # Marcar reclamo como requiere retiro de escombros
            cita.id_reclamo.requiere_retiro_escombros = True
            cita.id_reclamo.save()
        except Exception as e:
            messages.warning(request, f'Error al registrar escombro: {str(e)}')
    
    # Procesar evidencias/imágenes cargadas por el técnico
    idx = 0
    while True:
        archivo_key = f'evidencia_tecnico_{idx}'
        if archivo_key not in request.FILES:
            break
        archivo = request.FILES.get(archivo_key)
        descripcion = request.POST.get(f'descripcion_evidencia_{idx}', '').strip()
        if archivo:
            try:
                # Preservar nombre original del archivo
                nombre_original = archivo.name
                archivo.name = nombre_original
                
                # Determinar tipo de archivo
                content_type = getattr(archivo, 'content_type', '')
                tipo = 'image' if content_type.startswith('image/') else 'video'
                
                ArchivoEvidencia.objects.create(
                    id_reclamo=cita.id_reclamo,
                    archivo=archivo,
                    descripcion=descripcion,
                    tipo=tipo,
                    nombre_original=nombre_original,
                    fecha_subida=timezone.now(),
                    subido_por='tecnico',
                )
            except Exception as e:
                messages.warning(request, f'Error al guardar evidencia: {str(e)}')
        idx += 1
    
    # Procesar otros campos del formulario
    solucion = request.POST.get('solucion_aplicada', '').strip()
    marcar_resuelto = request.POST.get('marcar_resuelto')

    # Guardar fecha de cierre y calcular duración
    visita.fecha_cierre = timezone.now()
    visita.save()
    horas_trabajadas = None
    if visita.fecha_visita and visita.fecha_cierre:
        delta = visita.fecha_cierre - visita.fecha_visita
        horas_trabajadas = round(delta.total_seconds() / 3600, 2)
        reclamo = cita.id_reclamo
        reclamo.horas_trabajadas = horas_trabajadas
        reclamo.save()

    cita.estado = 'completada'
    cita.save()
    reclamo = cita.id_reclamo
    
    # Cambiar estado del reclamo según el checkbox
    if marcar_resuelto:
        reclamo.estado = 'resuelto'
        reclamo.fecha_resolucion = timezone.now()
        
        # Enviar encuesta automáticamente
        from django.core.mail import send_mail
        from .models import EncuestaSatisfaccion
        
        # Link de encuesta (Google Forms)
        link_encuesta = "https://docs.google.com/forms/d/e/1FAIpQLSeOxOpCzEeHzAZ16R3vMK0WGngJQw20mg2g7-auFMYrnX30cg/viewform?usp=dialog"
        
        try:
            # Crear registro de encuesta
            encuesta = EncuestaSatisfaccion.objects.create(
                id_reclamo=reclamo,
                email_propietario=reclamo.id_cliente.email,
                nombre_propietario=reclamo.id_cliente.nombre,
                link_encuesta=link_encuesta,
                estado='enviada',
                fecha_envio=timezone.now()
            )
            
            # Enviar email con encuesta
            asunto = f'Encuesta de Satisfacción - Reclamo #{reclamo.numero_folio}'
            mensaje = f"""
Estimado/a {reclamo.id_cliente.nombre},

Le agradecemos la confianza depositada en nuestros servicios. Esperamos que haya quedado satisfecho con la reparación realizada en su propiedad.

Para garantizar la calidad de nuestro trabajo y mejorar continuamente, lo invitamos a completar nuestra encuesta de satisfacción. Le tomará aproximadamente 2 minutos:

{link_encuesta}

Su retroalimentación es fundamental para nosotros.

Agradecemos sinceramente su tiempo y participación.

Saludos cordiales,
Equipo Postventa Pro
            """
            
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email='pabloslash21@gmail.com',
                recipient_list=[reclamo.id_cliente.email],
                fail_silently=True,  # No bloquear si falla el email
            )
        except Exception as e:
            # Log del error pero continuar con el cierre del reclamo
            print(f"Error al enviar encuesta: {str(e)}")
    elif reclamo.estado == 'asignado':
        # Si el reclamo está "asignado" y se completa la cita sin marcar como resuelto,
        # cambiar a "en_proceso" para indicar que ya se ha visitado
        reclamo.estado = 'en_proceso'
    
    if solucion:
        reclamo.resolucion = solucion
    reclamo.save()
    
    # Mensaje con estado del reclamo
    if marcar_resuelto:
        mensaje = f'✓ Cita completada. Estado del reclamo {reclamo.numero_folio}: RECLAMO RESUELTO'
    else:
        mensaje = f'✓ Cita completada para el reclamo {reclamo.numero_folio}. Materiales registrados.'
    
    messages.success(request, mensaje)
    return redirect('tecnico_detalle_reclamo', reclamo_id=reclamo.id_reclamo)


# ========================================
# GESTIÓN DE ESCOMBROS - TÉCNICO
# ========================================

@login_required
def tecnico_historial_escombros(request):
    """Listar historial de escombros del técnico con filtros por estado"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico asociada a este usuario.')
        return redirect('dashboard_tecnico')
    
    from .models import GestionEscombros
    
    # Obtener todos los escombros asociados a citas del técnico
    escombros = GestionEscombros.objects.filter(
        id_reclamo__tecnico_asignado=tecnico
    ).select_related(
        'id_reclamo', 'id_visita'
    ).order_by('-id_escombro')
    
    # Filtrar por estado si viene en GET
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        escombros = escombros.filter(estado=estado_filtro)
    
    context = {
        'escombros': escombros,
        'estado_filtro': estado_filtro,
        'estados': [
            ('pendiente', 'Pendiente'),
            ('programado', 'Programado'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
    }
    return render(request, 'tecnico/historial_escombros.html', context)


@login_required
def tecnico_actualizar_escombro(request, escombro_id):
    """Actualizar estado y detalles de un escombro"""
    tecnico = get_tecnico_from_user(request.user)
    if not tecnico:
        messages.error(request, 'No se encontró información de técnico.')
        return redirect('dashboard_tecnico')
    
    from .models import GestionEscombros
    
    escombro = get_object_or_404(GestionEscombros, id_escombro=escombro_id)
    
    # Verificar que el escombro pertenece a un reclamo del técnico
    if escombro.id_reclamo and escombro.id_reclamo.tecnico_asignado != tecnico and not request.user.is_staff:
        messages.error(request, 'No tienes permiso para actualizar este escombro.')
        return redirect('tecnico_historial_escombros')
    
    if request.method == 'POST':
        # Actualizar datos
        nuevo_estado = request.POST.get('estado', escombro.estado)
        fecha_programada = request.POST.get('fecha_programada_retiro', '')
        ubicacion = request.POST.get('ubicacion_exacta', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        
        escombro.estado = nuevo_estado
        escombro.ubicacion_exacta = ubicacion
        if fecha_programada:
            try:
                escombro.fecha_programada_retiro = fecha_programada
            except:
                pass
        escombro.observaciones = observaciones
        
        escombro.save()
        messages.success(request, f'Escombro actualizado correctamente.')
        return redirect('tecnico_historial_escombros')
    
    context = {
        'escombro': escombro,
        'estados': [
            ('pendiente', 'Pendiente'),
            ('programado', 'Programado'),
            ('en_ejecucion', 'En Ejecución'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
    }
    return render(request, 'tecnico/actualizar_escombro.html', context)


# ========================================
# COMPATIBILIDAD CON CÓDIGO ANTIGUO
# ========================================

# Alias para mantener compatibilidad
get_propietario_from_user = get_cliente_from_user


# ========================================
# VISTAS DEL SUPERVISOR
# ========================================

def get_supervisor_from_user(user):
    """Obtener al supervisor asociado al usuario autenticado"""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    
    try:
        perfil = user.perfil
        if perfil.rol == 'supervisor':
            return perfil
    except Exception:
        pass
    
    return None


@login_required
def dashboard_supervisor(request):
    """Dashboard principal del supervisor con indicadores operativos - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor o no tienes proyecto asignado.')
        return redirect('login')
    
    # Actualizar datos desde la BD
    supervisor.refresh_from_db()
    proyecto = supervisor.proyecto
    
    # Obtener estadísticas del proyecto
    # Estados abiertos: ingresado, asignado, en_ejecucion, en_proceso
    # Estados resueltos: resuelto, completado
    # Estados cancelados: cancelado
    reclamos_abiertos = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso']
    ).count()
    reclamos_resueltos = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['resuelto', 'completado']
    ).count()
    reclamos_total = Reclamo.objects.filter(proyecto=proyecto).count()
    
    # Reclamos con retraso (más de 7 días sin resolver)
    hace_7_dias = timezone.now() - timedelta(days=7)
    reclamos_retraso = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso'],
        fecha_ingreso__lt=hace_7_dias
    ).count()
    
    # Encuestas completadas del proyecto (con respuesta registrada)
    try:
        encuestas_completadas = EncuestaSatisfaccion.objects.filter(
            id_reclamo__proyecto=proyecto,
            fecha_respuesta__isnull=False
        ).count()
    except:
        encuestas_completadas = 0
    
    # Promedio de satisfacción del proyecto
    try:
        promedio_satisfaccion = EncuestaSatisfaccion.objects.filter(
            id_reclamo__proyecto=proyecto,
            fecha_respuesta__isnull=False,
            puntuacion__isnull=False
        ).aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
    except:
        promedio_satisfaccion = 0
    
    # Calcular tasa de resolución
    tasa_resolucion = (reclamos_resueltos / reclamos_total * 100) if reclamos_total > 0 else 0
    
    # Datos para gráfico de tendencia mensual (todos los días del mes)
    hoy = date.today()
    primer_dia_mes = date(hoy.year, hoy.month, 1)
    
    # Datos para gráfico: Reclamos por estado (mes actual)
    reclamos_ingresados = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso'],
        fecha_ingreso__gte=timezone.make_aware(datetime.combine(primer_dia_mes, datetime.min.time()))
    ).count()
    reclamos_en_proceso_graf = reclamos_ingresados  # Mismo conjunto
    reclamos_resueltos_graf = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['resuelto', 'completado'],
        fecha_ingreso__gte=timezone.make_aware(datetime.combine(primer_dia_mes, datetime.min.time()))
    ).count()
    reclamos_cancelados = Reclamo.objects.filter(
        proyecto=proyecto,
        estado='cancelado',
        fecha_ingreso__gte=timezone.make_aware(datetime.combine(primer_dia_mes, datetime.min.time()))
    ).count()
    tendencia_mensual = Reclamo.objects.filter(
        proyecto=proyecto,
        fecha_ingreso__gte=timezone.make_aware(datetime.combine(primer_dia_mes, datetime.min.time())),
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado']
    ).exclude(estado='cancelado').annotate(
        fecha=TruncDate('fecha_ingreso')
    ).values('fecha').annotate(count=Count('id_reclamo')).order_by('fecha')
    
    # Crear diccionario con todos los días del mes
    dias_en_mes = calendar.monthrange(hoy.year, hoy.month)[1]
    datos_mes = {}
    for dia in range(1, dias_en_mes + 1):
        fecha_dia = date(hoy.year, hoy.month, dia)
        datos_mes[fecha_dia] = 0
    
    # Llenar con datos reales
    for item in tendencia_mensual:
        if item['fecha']:
            datos_mes[item['fecha']] = item['count']
    
    # Preparar etiquetas y valores
    labels_tendencia = [str(dia) for dia in range(1, dias_en_mes + 1)]
    valores_tendencia = [datos_mes.get(date(hoy.year, hoy.month, dia), 0) for dia in range(1, dias_en_mes + 1)]
    
    # Nombre del mes actual
    nombre_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    mes_actual = nombre_meses[hoy.month - 1]
    
    # Datos para gráfico: Reclamos por especialidad (TODAS las especialidades)
    todas_especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener reclamos por especialidad
    reclamos_por_especialidad = Reclamo.objects.filter(
        proyecto=proyecto,
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado']
    ).exclude(estado='cancelado').values('categoria__nombre', 'categoria_id').annotate(
        count=Count('id_reclamo')
    ).order_by('categoria__nombre')
    
    # Crear diccionario con conteos
    conteos_especialidad = {}
    for item in reclamos_por_especialidad:
        nombre = item['categoria__nombre'] or 'Sin Especialidad'
        conteos_especialidad[nombre] = item['count']
    
    # Crear listas con TODAS las especialidades
    labels_especialidad = []
    valores_especialidad = []
    for esp in todas_especialidades:
        labels_especialidad.append(esp.nombre)
        valores_especialidad.append(conteos_especialidad.get(esp.nombre, 0))
    
    # Agregar "Sin Especialidad" si hay reclamos sin especialidad
    sin_esp_count = Reclamo.objects.filter(
        proyecto=proyecto,
        categoria__isnull=True,
        estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado']
    ).exclude(estado='cancelado').count()
    if sin_esp_count > 0:
        labels_especialidad.append('Sin Especialidad')
        valores_especialidad.append(sin_esp_count)
    
    # Crear lista de tuplas para el template
    especialidades_datos = list(zip(labels_especialidad, valores_especialidad))
    
    context = {
        'supervisor': supervisor,
        'proyecto': proyecto,
        'reclamos_abiertos': reclamos_abiertos,
        'reclamos_resueltos': reclamos_resueltos,
        'reclamos_total': reclamos_total,
        'reclamos_retraso': reclamos_retraso,
        'encuestas_completadas': encuestas_completadas,
        'promedio_satisfaccion': round(promedio_satisfaccion, 2),
        'tasa_resolucion': round(tasa_resolucion, 1),
        # Datos gráfico
        'reclamos_ingresados': reclamos_ingresados,
        'reclamos_en_proceso': reclamos_en_proceso_graf,
        'reclamos_resueltos_graf': reclamos_resueltos_graf,
        'reclamos_cancelados': reclamos_cancelados,
        'labels_tendencia': labels_tendencia,
        'valores_tendencia': valores_tendencia,
        'labels_especialidad': labels_especialidad,
        'valores_especialidad': valores_especialidad,
        'especialidades_datos': especialidades_datos,
        'mes_actual': mes_actual,
    }
    
    return render(request, 'supervisor/dashboard.html', context)


@login_required
def dashboard_kpis(request):
    """Dashboard de KPIs - Visualización completa de los 15 KPIs"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor o no tienes proyecto asignado.')
        return redirect('login')
    
    # Obtener filtros de fecha (opcional)
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    fecha_inicio = None
    fecha_fin = None
    
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except:
            pass
    
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Obtener todos los KPIs filtrados por proyecto del supervisor
    kpis_data = KPICalculator.obtener_todos_los_kpis(supervisor.proyecto, fecha_inicio, fecha_fin)
    
    # Mapeo de nombres descriptivos y categorías
    kpi_info = {
        "KPI_01": {
            "nombre": "Tasa Reclamos Atendidos en Plazo",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de reclamos atendidos dentro del plazo comprometido"
        },
        "KPI_02": {
            "nombre": "Ratio Demanda vs Capacidad",
            "categoria": "Capacidad",
            "descripcion": "Relación entre demanda y capacidad de técnicos (overbooking)"
        },
        "KPI_03": {
            "nombre": "Tiempo Promedio Resolución",
            "categoria": "Eficiencia",
            "descripcion": "TTR: Tiempo promedio para resolver un reclamo"
        },
        "KPI_04": {
            "nombre": "Cumplimiento de Citas",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de citas programadas que se cumplen"
        },
        "KPI_05": {
            "nombre": "Casos Cerrados en Primera Visita",
            "categoria": "Eficiencia",
            "descripcion": "Porcentaje de reclamos resueltos en la primera visita"
        },
        "KPI_06": {
            "nombre": "Tasa Reaperturas",
            "categoria": "Calidad",
            "descripcion": "Porcentaje de reclamos que se reabren después de cerrados"
        },
        "KPI_07": {
            "nombre": "Costo Promedio por Reclamo",
            "categoria": "Costo",
            "descripcion": "Costo total invertido por reclamo"
        },
        "KPI_08": {
            "nombre": "Costo Materiales por Caso",
            "categoria": "Costo",
            "descripcion": "Costo de materiales utilizados por caso"
        },
        "KPI_09": {
            "nombre": "Índice Frecuencia Tipos Falla",
            "categoria": "Análisis",
            "descripcion": "Distribución de tipos de falla más comunes"
        },
        "KPI_10": {
            "nombre": "Puntualidad del Técnico",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de citas donde el técnico llega a tiempo"
        },
        "KPI_11": {
            "nombre": "Productividad Técnico",
            "categoria": "Productividad",
            "descripcion": "Promedio de reclamos resueltos por técnico"
        },
        "KPI_12": {
            "nombre": "Estado de Reclamos",
            "categoria": "Análisis",
            "descripcion": "Reclamos pendientes y resueltos"
        },
        "KPI_13": {
            "nombre": "Tiempo Cierre Documental",
            "categoria": "Eficiencia",
            "descripcion": "Tiempo para completar la documentación del reclamo"
        },
        "KPI_14": {
            "nombre": "Satisfacción del Cliente",
            "categoria": "Satisfacción",
            "descripcion": "Porcentaje de clientes satisfechos por proyecto"
        },
        "KPI_15": {
            "nombre": "Costo Reprocesos",
            "categoria": "Costo",
            "descripcion": "Porcentaje de costo invertido en reprocesos"
        }
    }
    
    # Construir lista de KPIs con información completa
    kpis_formateados = []
    
    for kpi_id in ["KPI_01", "KPI_02", "KPI_03", "KPI_04", "KPI_05", 
                   "KPI_06", "KPI_07", "KPI_08", "KPI_09", "KPI_10",
                   "KPI_11", "KPI_12", "KPI_13", "KPI_14", "KPI_15"]:
        
        kpi_data = kpis_data.get(kpi_id, {})
        
        info = kpi_info.get(kpi_id, {})
        
        valor = kpi_data.get('valor', None)
        unidad = kpi_data.get('unidad', '')
        
        # Casos especiales de KPIs con estructura compleja
        datos_adicionales = {k: v for k, v in kpi_data.items() if k not in ['valor', 'unidad']}
        
        # Para KPI_09, si tiene categorias pero no valor, usar el porcentaje más alto
        if kpi_id == 'KPI_09' and 'categorias' in kpi_data:
            # Limpiar categorías sin nombre y ordenar (sin recortar a top 3)
            categorias = [c for c in kpi_data.get('categorias', []) if c.get('categoria')]
            categorias = sorted(categorias, key=lambda x: x.get('porcentaje', 0), reverse=True)
            kpi_data['categorias'] = categorias
            if valor is None and categorias:
                # Usar el porcentaje máximo entre las categorías válidas
                valor = categorias[0].get('porcentaje', 0)
        
        # Para KPI_11, si tiene tecnicos pero no valor, calcular promedio
        if kpi_id == 'KPI_11' and 'tecnicos' in kpi_data and valor is None:
            tecnicos = kpi_data.get('tecnicos', [])
            if tecnicos:
                total_reclamos = sum([t.get('reclamos', 0) for t in tecnicos])
                promedio = total_reclamos / len(tecnicos) if tecnicos else 0
                valor = round(promedio, 2)
                unidad = 'reclamos/técnico'
        
        # Para KPI_12, si tiene proyectos pero no valor, calcular demanda total
        if kpi_id == 'KPI_12' and 'proyectos' in kpi_data and valor is None:
            proyectos = kpi_data.get('proyectos', [])
            if proyectos:
                total_reclamos = sum([p.get('cantidad', 0) for p in proyectos])
                valor = total_reclamos if total_reclamos > 0 else None
                unidad = 'reclamos'
        
        # Para KPI_14, si tiene proyectos pero no valor, calcular satisfacción promedio
        if kpi_id == 'KPI_14' and 'proyectos' in kpi_data and valor is None:
            proyectos = kpi_data.get('proyectos', [])
            if proyectos:
                total_satisfaccion = sum([p.get('satisfaccion', 0) for p in proyectos])
                promedio = total_satisfaccion / len(proyectos) if proyectos else 0
                valor = round(promedio, 2)
                unidad = '%'
        
        kpis_formateados.append({
            'id': kpi_id,
            'nombre': info.get('nombre', kpi_id),
            'categoria': info.get('categoria', 'Otros'),
            'descripcion': info.get('descripcion', ''),
            'valor': valor,
            'unidad': unidad,
            'datos_adicionales': datos_adicionales
        })
    
    # Agrupar por categoría
    kpis_por_categoria = {}
    for kpi in kpis_formateados:
        cat = kpi['categoria']
        if cat not in kpis_por_categoria:
            kpis_por_categoria[cat] = []
        kpis_por_categoria[cat].append(kpi)
    
    # Formatear fechas a DD/MM/YYYY para mostrar en el template
    fecha_inicio_display = fecha_inicio.strftime('%d/%m/%Y') if fecha_inicio else None
    fecha_fin_display = fecha_fin.strftime('%d/%m/%Y') if fecha_fin else None

    # (Sección de tendencia mensual movida al final de admin_reportes)
    
    context = {
        'supervisor': supervisor,
        'kpis': kpis_formateados,
        'kpis_por_categoria': kpis_por_categoria,
        'fecha_inicio': fecha_inicio_display,
        'fecha_fin': fecha_fin_display,
        'fecha_inicio_input': fecha_inicio_str,  # Para mantener en el input del formulario
        'fecha_fin_input': fecha_fin_str,        # Para mantener en el input del formulario
        'categorias': list(kpis_por_categoria.keys()),
    }
    
    return render(request, 'supervisor/kpis_dashboard.html', context)


@login_required
def supervisor_reclamos(request):
    """Supervisión de reclamos con filtros - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor o no tienes proyecto asignado.')
        return redirect('login')
    
    proyecto = supervisor.proyecto
    
    # Obtener reclamos del proyecto
    reclamos = Reclamo.objects.filter(proyecto=proyecto).select_related(
        'propietario',
        'tecnico_asignado',
        'proyecto'
    ).prefetch_related('citas')
    
    # Filtros
    estado = request.GET.get('estado')
    tecnico_id = request.GET.get('tecnico')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        reclamos = reclamos.filter(estado=estado)
    
    if tecnico_id:
        reclamos = reclamos.filter(tecnico_asignado_id=tecnico_id)
    
    if fecha_desde:
        try:
            fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            reclamos = reclamos.filter(fecha_ingreso__date__gte=fecha)
        except:
            pass
    
    if fecha_hasta:
        try:
            fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            reclamos = reclamos.filter(fecha_ingreso__date__lte=fecha)
        except:
            pass
    
    # Marcar reclamos con retraso
    hace_7_dias = timezone.now() - timedelta(days=7)
    reclamos_con_retraso = set()
    
    for reclamo in reclamos:
        if reclamo.estado in ['ingresado', 'asignado', 'en_ejecucion', 'en_proceso']:
            if reclamo.fecha_ingreso and reclamo.fecha_ingreso < hace_7_dias:
                reclamos_con_retraso.add(reclamo.id_reclamo)
    
    # Opciones para filtros (técnicos de la misma constructora del proyecto)
    tecnicos = Tecnico.objects.filter(
        constructora=proyecto.constructora,
        especialidad__isnull=False
    ).distinct().order_by('user__first_name')
    
    estados = [
        ('ingresado', 'Ingresado'),
        ('asignado', 'Asignado'),
        ('en_ejecucion', 'En Ejecución'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('resuelto', 'Reclamo Resuelto'),
        ('cancelado', 'Cancelado'),
    ]
    
    context = {
        'supervisor': supervisor,
        'proyecto': proyecto,
        'reclamos': reclamos.order_by('-fecha_ingreso'),
        'tecnicos': tecnicos,
        'estados': estados,
        'reclamos_con_retraso': reclamos_con_retraso,
        'filtros_activos': bool(estado or tecnico_id or fecha_desde or fecha_hasta),
    }
    
    return render(request, 'supervisor/reclamos.html', context)


@login_required
def supervisor_detalle_reclamo(request, reclamo_id):
    """Detalle de un reclamo para supervisor - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor o no tienes proyecto asignado.')
        return redirect('login')
    
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    
    # Verificar que el reclamo pertenece al proyecto del supervisor
    if reclamo.proyecto != supervisor.proyecto:
        messages.error(request, 'No tienes acceso a este reclamo.')
        return redirect('dashboard_supervisor')
    
    # Obtener todos los datos relacionados
    citas = reclamo.citas.all()
    encuestas = reclamo.encuestas.all()
    archivos_evidencia = reclamo.archivos_evidencia.all()
    visitas_tecnicas = reclamo.visitas_tecnicas.all()
    gestiones_escombros = reclamo.gestion_escombros.all()
    
    # Obtener materiales usados en todas las visitas técnicas del reclamo
    from postventa_app.models import UsoMaterial
    materiales_usados = UsoMaterial.objects.filter(id_visita__id_reclamo=reclamo)
    
    # Calcular total para cada material
    for material_uso in materiales_usados:
        if material_uso.cantidad_usada and material_uso.id_material.costo_unitario:
            material_uso.total = material_uso.cantidad_usada * material_uso.id_material.costo_unitario
        else:
            material_uso.total = 0
    
    # Calcular duración de cada visita técnica
    for visita in visitas_tecnicas:
        if visita.fecha_visita and visita.fecha_cierre:
            duracion = visita.fecha_cierre - visita.fecha_visita
            # Convertir a minutos
            visita.duracion_calculada = int(duracion.total_seconds() / 60)
        else:
            visita.duracion_calculada = None
    
    context = {
        'supervisor': supervisor,
        'reclamo': reclamo,
        'citas': citas,
        'encuestas': encuestas,
        'archivos_evidencia': archivos_evidencia,
        'visitas_tecnicas': visitas_tecnicas,
        'gestiones_escombros': gestiones_escombros,
        'materiales_usados': materiales_usados,
    }
    
    return render(request, 'supervisor/detalle_reclamo.html', context)


# ================================================================
# VISTAS DE VALIDACIÓN DE RETIRO DE ESCOMBROS (HU-SUP-03)
# ================================================================

@login_required
def supervisor_validar_escombros(request):
    """Vista para validar y aprobar retiro de escombros - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor o no tienes proyecto asignado.')
        return redirect('login')
    
    proyecto = supervisor.proyecto
    
    # Obtener solicitudes de escombros pendientes del proyecto
    solicitudes_escombros = GestionEscombros.objects.filter(
        id_reclamo__proyecto=proyecto,
        estado__in=['pendiente', 'programado']
    ).select_related(
        'id_reclamo',
        'id_visita'
    ).order_by('-id_escombro')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        solicitudes_escombros = solicitudes_escombros.filter(estado=estado)
    
    context = {
        'supervisor': supervisor,
        'proyecto': proyecto,
        'solicitudes_escombros': solicitudes_escombros,
        'estados': [
            ('pendiente', 'Pendiente'),
            ('programado', 'Programado'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
    }
    
    return render(request, 'supervisor/validar_escombros.html', context)


@login_required
def supervisor_procesar_escombro(request, escombro_id):
    """Procesar (aprobar/rechazar) una solicitud de retiro de escombros con asignación de técnicos o empresa"""
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso como supervisor.')
        return redirect('login')
    
    escombro = get_object_or_404(GestionEscombros, id_escombro=escombro_id)
    
    # Verificar que el escombro pertenece al proyecto del supervisor
    if escombro.id_reclamo.proyecto != supervisor.proyecto:
        messages.error(request, 'No tienes acceso a esta solicitud.')
        return redirect('supervisor_validar_escombros')
    
    # Obtener empresas de retiro activas
    empresas_retiro = EmpresaRetiro.objects.filter(activa=True).order_by('nombre')
    
    # Obtener técnicos disponibles del proyecto (por constructora)
    tecnicos_disponibles = Tecnico.objects.filter(
        especialidad__isnull=False,
        constructora=supervisor.proyecto.constructora
    ).select_related('especialidad', 'constructora').order_by('nombre')
    
    # Obtener asignaciones ya existentes para este escombro
    asignaciones_existentes = AsignacionEscombros.objects.filter(
        id_escombro=escombro
    ).select_related('id_tecnico')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')
        tipo_retiro = request.POST.get('tipo_retiro')  # 'empresa' o 'tecnicos'
        
        if accion == 'aprobar':
            if tipo_retiro == 'empresa':
                # Retiro por empresa externa
                empresa_id = request.POST.get('empresa_retiro')
                
                if not empresa_id:
                    messages.warning(request, 'Debes seleccionar una empresa de retiro.')
                    context = {
                        'supervisor': supervisor,
                        'escombro': escombro,
                        'reclamo': escombro.id_reclamo,
                        'empresas_retiro': empresas_retiro,
                        'tecnicos_disponibles': tecnicos_disponibles,
                        'tecnicos_asignados': asignaciones_existentes.values_list('id_tecnico_id', flat=True),
                    }
                    return render(request, 'supervisor/procesar_escombro.html', context)
                
                try:
                    empresa = EmpresaRetiro.objects.get(id_empresa=empresa_id)
                except EmpresaRetiro.DoesNotExist:
                    messages.error(request, 'Empresa de retiro no válida.')
                    context = {
                        'supervisor': supervisor,
                        'escombro': escombro,
                        'reclamo': escombro.id_reclamo,
                        'empresas_retiro': empresas_retiro,
                        'tecnicos_disponibles': tecnicos_disponibles,
                        'tecnicos_asignados': asignaciones_existentes.values_list('id_tecnico_id', flat=True),
                    }
                    return render(request, 'supervisor/procesar_escombro.html', context)
                
                # Eliminar asignaciones de técnicos previas si las hay
                asignaciones_existentes.delete()
                
                # Asignar empresa
                escombro.id_empresa_retiro = empresa
                escombro.estado = 'programado'
                escombro.observaciones = observaciones
                escombro.save()
                messages.success(request, f'Solicitud de escombros #{escombro.id_escombro} aprobada. Empresa: {empresa.nombre}')
                
            elif tipo_retiro == 'tecnicos':
                # Retiro por técnicos internos
                tecnico_ids = request.POST.getlist('tecnicos')
                
                if not tecnico_ids:
                    messages.warning(request, 'Debes seleccionar al menos un técnico para el retiro.')
                    context = {
                        'supervisor': supervisor,
                        'escombro': escombro,
                        'reclamo': escombro.id_reclamo,
                        'empresas_retiro': empresas_retiro,
                        'tecnicos_disponibles': tecnicos_disponibles,
                        'tecnicos_asignados': asignaciones_existentes.values_list('id_tecnico_id', flat=True),
                    }
                    return render(request, 'supervisor/procesar_escombro.html', context)
                
                # Validar que todos los técnicos pertenezcan al proyecto
                for tecnico_id in tecnico_ids:
                    tecnico = get_object_or_404(Tecnico, id_tecnico=tecnico_id)
                    if tecnico.constructora != supervisor.proyecto.constructora:
                        messages.error(request, 'Uno o más técnicos no pertenecen a tu proyecto.')
                        context = {
                            'supervisor': supervisor,
                            'escombro': escombro,
                            'reclamo': escombro.id_reclamo,
                            'empresas_retiro': empresas_retiro,
                            'tecnicos_disponibles': tecnicos_disponibles,
                            'tecnicos_asignados': asignaciones_existentes.values_list('id_tecnico_id', flat=True),
                        }
                        return render(request, 'supervisor/procesar_escombro.html', context)
                
                # Eliminar asignaciones previas
                asignaciones_existentes.delete()
                
                # Crear nuevas asignaciones
                for tecnico_id in tecnico_ids:
                    tecnico = Tecnico.objects.get(id_tecnico=tecnico_id)
                    AsignacionEscombros.objects.create(
                        id_escombro=escombro,
                        id_tecnico=tecnico,
                        estado='asignado'
                    )
                
                # Limpiar empresa si estaba asignada
                escombro.id_empresa_retiro = None
                # Aprobar el escombro
                escombro.estado = 'programado'
                escombro.observaciones = observaciones
                escombro.save()
                messages.success(request, f'Solicitud de escombros #{escombro.id_escombro} aprobada y {len(tecnico_ids)} técnico(s) asignado(s).')
            else:
                messages.warning(request, 'Debes seleccionar un tipo de retiro (empresa o técnicos).')
                context = {
                    'supervisor': supervisor,
                    'escombro': escombro,
                    'reclamo': escombro.id_reclamo,
                    'empresas_retiro': empresas_retiro,
                    'tecnicos_disponibles': tecnicos_disponibles,
                    'tecnicos_asignados': asignaciones_existentes.values_list('id_tecnico_id', flat=True),
                }
                return render(request, 'supervisor/procesar_escombro.html', context)
            
        elif accion == 'rechazar':
            escombro.estado = 'cancelado'
            escombro.observaciones = observaciones
            escombro.save()
            # Eliminar asignaciones si existían
            asignaciones_existentes.delete()
            messages.warning(request, f'Solicitud de escombros #{escombro.id_escombro} rechazada.')
        
        return redirect('supervisor_validar_escombros')
    
    # Obtener IDs de técnicos ya asignados
    tecnicos_asignados = asignaciones_existentes.values_list('id_tecnico_id', flat=True)
    
    context = {
        'supervisor': supervisor,
        'escombro': escombro,
        'reclamo': escombro.id_reclamo,
        'empresas_retiro': empresas_retiro,
        'tecnicos_disponibles': tecnicos_disponibles,
        'asignaciones_existentes': asignaciones_existentes,
        'tecnicos_asignados': tecnicos_asignados,
    }
    
    return render(request, 'supervisor/procesar_escombro.html', context)


# ================================================================
# HU-SUP-04: ASIGNACIÓN DE EQUIPO PARA RETIRO DE ESCOMBROS
# ================================================================

@login_required

# ================================================================
# HU-SUP-05: REVISIÓN DE EVIDENCIA FOTOGRÁFICA
# ================================================================

@login_required
def supervisor_evidencia_fotografica(request):
    """Vista para revisar evidencia fotográfica de reclamos - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    proyecto = supervisor.proyecto
    
    # Obtener reclamos del proyecto con archivos de evidencia
    reclamos_con_fotos = Reclamo.objects.filter(
        proyecto=proyecto,
        archivos_evidencia__isnull=False
    ).distinct().select_related('propietario').order_by('-id_reclamo')
    
    # Filtrar por estado si está en el request
    estado_reclamo = request.GET.get('estado', '')
    if estado_reclamo:
        reclamos_con_fotos = reclamos_con_fotos.filter(estado=estado_reclamo)
    
    # Filtrar por quién subió la evidencia
    subido_por = request.GET.get('subido_por', '')
    
    context = {
        'supervisor': supervisor,
        'reclamos_con_fotos': reclamos_con_fotos,
        'estado_reclamo': estado_reclamo,
        'subido_por': subido_por,
    }
    
    return render(request, 'supervisor/evidencia_fotografica.html', context)


@login_required
def supervisor_detalle_evidencia(request, reclamo_id):
    """Vista para ver galería de fotos antes/después de un reclamo"""
    supervisor = get_supervisor_from_user(request.user)
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    proyecto = supervisor.proyecto
    
    # Verificar que el reclamo pertenece al proyecto del supervisor
    if reclamo.proyecto != proyecto:
        messages.error(request, 'No tienes permiso para ver esta evidencia.')
        return redirect('supervisor_evidencia_fotografica')
    
    # Obtener archivos de evidencia organizados por tipo/subido_por
    archivos_evidencia = ArchivoEvidencia.objects.filter(
        id_reclamo=reclamo
    ).order_by('descripcion', 'fecha_subida')
    
    # Separar por tipo de usuario que subió
    fotos_cliente = archivos_evidencia.filter(subido_por='cliente')
    fotos_tecnico = archivos_evidencia.filter(subido_por='tecnico')
    fotos_sistema = archivos_evidencia.filter(subido_por='sistema')
    
    # Obtener visita técnica asociada si existe
    visita_tecnica = VisitaTecnica.objects.filter(id_reclamo=reclamo).first()
    
    context = {
        'supervisor': supervisor,
        'reclamo': reclamo,
        'visita_tecnica': visita_tecnica,
        'archivos_evidencia': archivos_evidencia,
        'fotos_cliente': fotos_cliente,
        'fotos_tecnico': fotos_tecnico,
        'fotos_sistema': fotos_sistema,
    }
    
    return render(request, 'supervisor/detalle_evidencia.html', context)


# ================================================================
# HU-SUP-06: CONTROL DE MATERIALES USADOS
# ================================================================

@login_required
def supervisor_control_materiales(request):
    """Vista para revisar materiales usados en reparaciones - Por Proyecto"""
    supervisor = get_supervisor_from_user(request.user)
    proyecto = supervisor.proyecto
    
    # Obtener visitas técnicas del proyecto con materiales usados
    visitas_con_materiales = VisitaTecnica.objects.filter(
        id_reclamo__proyecto=proyecto,
        usos_materiales__isnull=False
    ).distinct().select_related('id_reclamo', 'id_tecnico').order_by('-fecha_visita')
    
    # Filtrar por reclamo si está en el request
    reclamo_id = request.GET.get('reclamo_id', '')
    if reclamo_id:
        visitas_con_materiales = visitas_con_materiales.filter(id_reclamo_id=reclamo_id)
    
    # Obtener estadísticas de materiales más usados
    materiales_stats = UsoMaterial.objects.filter(
        id_visita__id_reclamo__proyecto=proyecto
    ).values('id_material__nombre', 'id_material__unidad_medida', 'id_material__costo_unitario').annotate(
        total_usado=Sum('cantidad_usada'),
        cantidad_usos=Count('id_uso')
    ).order_by('-total_usado')
    
    # Calcular costo total de materiales usados
    costo_total_materiales = 0
    for stat in materiales_stats:
        if stat['id_material__costo_unitario'] and stat['total_usado']:
            costo_total_materiales += stat['id_material__costo_unitario'] * stat['total_usado']
    
    context = {
        'supervisor': supervisor,
        'visitas_con_materiales': visitas_con_materiales,
        'materiales_stats': materiales_stats,
        'costo_total_materiales': costo_total_materiales,
        'reclamo_id': reclamo_id,
    }
    
    return render(request, 'supervisor/control_materiales.html', context)


@login_required
def supervisor_detalle_materiales_visita(request, visita_id):
    """Vista para ver detalle de materiales usados en una visita técnica"""
    supervisor = get_supervisor_from_user(request.user)
    visita = get_object_or_404(VisitaTecnica, id_visita=visita_id)
    proyecto = supervisor.proyecto
    
    # Verificar que la visita pertenece a un reclamo del proyecto del supervisor
    if visita.id_reclamo.proyecto != proyecto:
        messages.error(request, 'No tienes permiso para ver estos materiales.')
        return redirect('supervisor_control_materiales')
    
    # Obtener materiales usados en esta visita
    usos_materiales = UsoMaterial.objects.filter(
        id_visita=visita
    ).select_related('id_material').order_by('fecha_uso')
    
    # Calcular costo total de esta visita
    costo_total_visita = 0
    for uso in usos_materiales:
        if uso.id_material.costo_unitario and uso.cantidad_usada:
            costo_total_visita += uso.id_material.costo_unitario * uso.cantidad_usada
    
    context = {
        'supervisor': supervisor,
        'visita': visita,
        'reclamo': visita.id_reclamo,
        'usos_materiales': usos_materiales,
        'costo_total_visita': costo_total_visita,
    }
    
    return render(request, 'supervisor/detalle_materiales_visita.html', context)


# ================================================================
# HU-SUP-07: DISPONIBILIDAD DE TÉCNICOS
# ================================================================

@login_required
def supervisor_disponibilidad_tecnicos(request):
    """Vista para revisar disponibilidad de técnicos - Por Proyecto"""
    from datetime import date, timedelta
    supervisor = get_supervisor_from_user(request.user)
    
    # Validar que sea supervisor
    if not supervisor or not supervisor.proyecto:
        messages.error(request, 'No tienes acceso a esta sección. Debes ser un supervisor con proyecto asignado.')
        return redirect('index')
    
    proyecto = supervisor.proyecto
    
    # Obtener técnicos del proyecto (por constructora)
    tecnicos = Tecnico.objects.filter(
        especialidad__isnull=False,
        constructora=proyecto.constructora
    ).select_related('especialidad', 'constructora').order_by('nombre')
    
    # Obtener disponibilidades para los próximos 90 días (3 meses)
    fecha_inicio = date.today()
    fecha_fin = fecha_inicio + timedelta(days=90)
    
    # Obtener disponibilidades puntuales (no recurrentes)
    disponibilidades_puntuales = Disponibilidad.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        es_recurrente=False,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('id_tecnico').order_by('fecha', 'hora_inicio')
    
    # Obtener disponibilidades recurrentes y expandirlas
    disponibilidades_recurrentes = Disponibilidad.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        es_recurrente=True
    ).select_related('id_tecnico')
    
    # Expandir disponibilidades recurrentes para el período de 90 días
    disponibilidades_expandidas = []
    for disp_rec in disponibilidades_recurrentes:
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            if fecha_actual.weekday() == disp_rec.dia_semana:
                # Crear una entrada expandida (no guardar en BD, solo para mostrar)
                disponibilidades_expandidas.append({
                    'id_disponibilidad': disp_rec.id_disponibilidad,
                    'id_tecnico': disp_rec.id_tecnico,
                    'tecnico_nombre': disp_rec.id_tecnico.nombre,
                    'fecha': fecha_actual,
                    'hora_inicio': disp_rec.hora_inicio,
                    'hora_fin': disp_rec.hora_fin,
                    'es_recurrente': True,
                })
            fecha_actual += timedelta(days=1)
    
    # Combinar disponibilidades puntuales y expandidas
    disponibilidades_list = list(disponibilidades_puntuales.values())
    disponibilidades_list.extend(disponibilidades_expandidas)
    
    # Ordenar por fecha
    disponibilidades_list.sort(key=lambda x: (x['fecha'], x['hora_inicio']))
    
    # Filtrar por técnico si está en el request
    tecnico_id = request.GET.get('tecnico_id', '')
    if tecnico_id:
        disponibilidades_list = [d for d in disponibilidades_list if str(d['id_tecnico'].id_tecnico) == tecnico_id]
    
    context = {
        'supervisor': supervisor,
        'tecnicos': tecnicos,
        'disponibilidades': disponibilidades_list,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'tecnico_id': tecnico_id,
    }
    
    return render(request, 'supervisor/disponibilidad_tecnicos.html', context)


@login_required
def supervisor_calendario_disponibilidad(request):
    """Vista con calendario de disponibilidad consolidada - Por Proyecto"""
    from datetime import date, timedelta
    supervisor = get_supervisor_from_user(request.user)
    proyecto = supervisor.proyecto
    
    # Obtener técnicos del proyecto
    tecnicos = Tecnico.objects.filter(
        especialidad__isnull=False,
        constructora=proyecto.constructora
    ).select_related('especialidad').order_by('nombre')
    
    # Rango de fechas (3 meses)
    fecha_inicio = date.today()
    fecha_fin = fecha_inicio + timedelta(days=90)
    
    # Obtener disponibilidades puntuales
    disponibilidades_puntuales = Disponibilidad.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        es_recurrente=False,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('id_tecnico').order_by('fecha', 'hora_inicio')
    
    # Obtener disponibilidades recurrentes y expandirlas
    disponibilidades_recurrentes = Disponibilidad.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        es_recurrente=True
    ).select_related('id_tecnico')
    
    # Expandir disponibilidades recurrentes
    disponibilidades_expandidas = []
    for disp_rec in disponibilidades_recurrentes:
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            if fecha_actual.weekday() == disp_rec.dia_semana:
                disponibilidades_expandidas.append({
                    'id_disponibilidad': disp_rec.id_disponibilidad,
                    'id_tecnico': disp_rec.id_tecnico,
                    'tecnico_nombre': disp_rec.id_tecnico.nombre,
                    'fecha': fecha_actual,
                    'hora_inicio': disp_rec.hora_inicio,
                    'hora_fin': disp_rec.hora_fin,
                    'es_recurrente': True,
                })
            fecha_actual += timedelta(days=1)
    
    # Combinar disponibilidades
    disponibilidades_list = list(disponibilidades_puntuales.values())
    disponibilidades_list.extend(disponibilidades_expandidas)
    disponibilidades_list.sort(key=lambda x: (x['fecha'], x['hora_inicio']))
    
    # Agrupar disponibilidades por fecha
    disponibilidades_por_fecha = {}
    for disp in disponibilidades_list:
        fecha_key = disp['fecha'].strftime('%Y-%m-%d')
        if fecha_key not in disponibilidades_por_fecha:
            disponibilidades_por_fecha[fecha_key] = []
        disponibilidades_por_fecha[fecha_key].append(disp)
    
    # Obtener asignaciones de escombros/citas para comparar
    asignaciones_escombros = AsignacionEscombros.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        estado__in=['asignado', 'aceptado']
    ).select_related('id_tecnico', 'id_escombro').order_by('fecha_asignacion')
    
    citas = Cita.objects.filter(
        id_tecnico__constructora=proyecto.constructora,
        estado__in=['confirmada', 'en_progreso']
    ).select_related('id_tecnico').order_by('fecha_cita')
    
    context = {
        'supervisor': supervisor,
        'tecnicos': tecnicos,
        'disponibilidades': disponibilidades_list,
        'disponibilidades_por_fecha': disponibilidades_por_fecha,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'asignaciones_escombros': asignaciones_escombros,
        'citas': citas,
    }
    
    return render(request, 'supervisor/calendario_disponibilidad.html', context)


# ================================================================
# API PARA POWER BI - EXPORTACIÓN DE KPIs
# ================================================================

@login_required
def api_kpis_export(request):
    """
    API que exporta todos los KPIs en formato JSON para Power BI.
    Parámetros opcionales:
    - proyecto_id: Filtrar por proyecto
    - fecha_inicio: Formato YYYY-MM-DD
    - fecha_fin: Formato YYYY-MM-DD
    - formato: 'json' (default) o 'csv'
    """
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor:
        return JsonResponse({"error": "No autorizado"}, status=403)
    
    # Parámetros de filtro
    proyecto_id = request.GET.get('proyecto_id')
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    formato = request.GET.get('formato', 'json')
    
    proyecto = None
    if proyecto_id:
        proyecto = get_object_or_404(Proyecto, id_proyecto=proyecto_id, id=supervisor.proyecto.id)
    else:
        proyecto = supervisor.proyecto
    
    # Parsear fechas
    fecha_inicio = None
    fecha_fin = None
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except:
            pass
    
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Obtener todos los KPIs
    kpis = KPICalculator.obtener_todos_los_kpis(proyecto, fecha_inicio, fecha_fin)
    
    if formato == 'csv':
        # Exportar en CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="kpis_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['KPI', 'Valor', 'Unidad', 'Detalles'])
        
        for kpi_name, kpi_data in kpis.items():
            if isinstance(kpi_data, dict):
                valor = kpi_data.get('valor', 'N/A')
                unidad = kpi_data.get('unidad', '')
                detalles = json.dumps({k: v for k, v in kpi_data.items() if k not in ['valor', 'unidad']})
                writer.writerow([kpi_name, valor, unidad, detalles])
        
        return response
    else:
        # Exportar en JSON (default)
        return JsonResponse({
            "proyecto": proyecto.nombre if proyecto else "Global",
            "fecha_inicio": fecha_inicio_str or "N/A",
            "fecha_fin": fecha_fin_str or "N/A",
            "kpis": kpis,
            "timestamp": timezone.now().isoformat()
        }, safe=False)


def api_kpis_export_public(request):
    """
    API pública SIN autenticación para Power BI.
    Exporta todos los KPIs en formato JSON NORMALIZADO (vertical).
    Formato ideal para Power BI.
    """
    # Parámetros de filtro
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    formato = request.GET.get('formato', 'json')
    
    # Parsear fechas
    fecha_inicio = None
    fecha_fin = None
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except:
            pass
    
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Obtener todos los KPIs
    kpis_data = KPICalculator.obtener_todos_los_kpis(None, fecha_inicio, fecha_fin)
    
    # Convertir a formato NORMALIZADO (vertical) para Power BI
    kpis_normalizados = []
    
    # Mapeo de nombres descriptivos para los KPIs
    kpi_nombres = {
        "KPI_01": "Tasa Reclamos Atendidos en Plazo",
        "KPI_02": "Ratio Demanda vs Capacidad",
        "KPI_03": "Tiempo Promedio Resolucion",
        "KPI_04": "Cumplimiento Citas",
        "KPI_05": "Casos Cerrados Primera Visita",
        "KPI_06": "Tasa Reaperturas",
        "KPI_07": "Costo Promedio Reclamo",
        "KPI_08": "Costo Materiales Caso",
        "KPI_09": "Frecuencia Tipos Falla",
        "KPI_10": "Puntualidad Tecnico",
        "KPI_11": "Productividad Tecnico",
        "KPI_12": "Demanda Proyecto",
        "KPI_13": "Tiempo Cierre Documental",
        "KPI_14": "Satisfaccion Cliente",
        "KPI_15": "Costo Reprocesos"
    }
    
    for kpi_id, kpi_data in kpis_data.items():
        if isinstance(kpi_data, dict):
            # Extraer valor y unidad
            valor = kpi_data.get('valor', None)
            unidad = kpi_data.get('unidad', '')
            
            # Crear fila normalizada
            fila = {
                "KPI_ID": kpi_id,
                "KPI_Nombre": kpi_nombres.get(kpi_id, kpi_id),
                "Valor": valor,
                "Unidad": unidad,
                "Fecha_Generacion": timezone.now().isoformat(),
            }
            
            # Agregar información adicional si existe
            if 'total' in kpi_data:
                fila['Total'] = kpi_data['total']
            if 'citas' in kpi_data:
                fila['Citas'] = kpi_data['citas']
            if 'tecnicos' in kpi_data:
                fila['Tecnicos'] = kpi_data['tecnicos']
            if 'error' in kpi_data:
                fila['Error'] = kpi_data['error']
            
            kpis_normalizados.append(fila)
    
    if formato == 'csv':
        # Exportar en CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="kpis_powerbi.csv"'
        
        if not kpis_normalizados:
            return response
        
        writer = csv.DictWriter(response, fieldnames=kpis_normalizados[0].keys())
        writer.writeheader()
        writer.writerows(kpis_normalizados)
        
        return response
    else:
        # Exportar en JSON NORMALIZADO - Como tabla plana directa
        # Agregar contexto a cada fila
        for fila in kpis_normalizados:
            fila['fecha_inicio'] = fecha_inicio_str or "N/A"
            fila['fecha_fin'] = fecha_fin_str or "N/A"
            fila['proyecto'] = 'Global'
        
        # Power BI entiende mejor una lista plana de records
        # Envolver en response que devuelve la lista directa
        response = JsonResponse(kpis_normalizados, safe=False)
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json'
        return response


# ================================================================
# VISTAS DEL ADMINISTRADOR
# ================================================================

def get_admin_from_user(user):
    """Obtener si el usuario es administrador"""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    
    # Administrador es un usuario con is_staff=True
    return user.is_staff


@login_required
def dashboard_admin(request):
    """Dashboard principal del administrador - Muestra datos de proyectos de su constructora"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil del administrador
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    # Obtener la constructora del administrador
    constructora = admin_perfil.proyecto.constructora
    
    # Obtener todos los proyectos de la constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    # Obtener el proyecto seleccionado (por GET o el primero por defecto)
    proyecto_id = request.GET.get('proyecto_id')
    if proyecto_id:
        proyecto = proyectos_constructora.filter(id=proyecto_id).first()
    
    # Si no hay proyecto seleccionado o no es válido, usar todos
    if not proyecto_id or not proyecto:
        proyecto = None
    
    # Calcular estadísticas
    if proyecto:
        # Mostrar solo del proyecto seleccionado
        reclamos_qs = Reclamo.objects.filter(proyecto=proyecto)
        propietarios_qs = Propietario.objects.filter(proyecto=proyecto)
        citas_qs = Cita.objects.filter(id_reclamo__proyecto=proyecto)
    else:
        # Mostrar de TODOS los proyectos de la constructora
        reclamos_qs = Reclamo.objects.filter(proyecto__in=proyectos_constructora)
        propietarios_qs = Propietario.objects.filter(proyecto__in=proyectos_constructora)
        citas_qs = Cita.objects.filter(id_reclamo__proyecto__in=proyectos_constructora)
    
    # Técnicos de la constructora (todos, no filtrados por proyecto)
    tecnicos_qs = Tecnico.objects.filter(constructora=constructora)
    
    total_reclamos = reclamos_qs.count()
    total_propietarios = propietarios_qs.count()
    total_tecnicos = tecnicos_qs.count()
    total_citas = citas_qs.count()
    
    # Reclamos por estado
    reclamos_pendientes = reclamos_qs.filter(estado='pendiente').count()
    reclamos_en_proceso = reclamos_qs.filter(estado__in=['asignado', 'en_proceso']).count()
    reclamos_resueltos = reclamos_qs.filter(estado='resuelto').count()
    
    # Citas completadas
    citas_completadas = citas_qs.filter(estado='completada').count()
    
    context = {
        'admin_perfil': admin_perfil,
        'constructora': constructora,
        'proyectos_constructora': proyectos_constructora,
        'proyecto_seleccionado': proyecto,
        'total_reclamos': total_reclamos,
        'total_propietarios': total_propietarios,
        'total_tecnicos': total_tecnicos,
        'total_citas': total_citas,
        'reclamos_pendientes': reclamos_pendientes,
        'reclamos_en_proceso': reclamos_en_proceso,
        'reclamos_resueltos': reclamos_resueltos,
        'citas_completadas': citas_completadas,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
def admin_reclamos(request):
    """Ver todos los reclamos del sistema"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    # Filtros
    estado = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')
    proyecto_id = request.GET.get('proyecto', '')
    especialidad_id = request.GET.get('especialidad', '')
    tecnico_id = request.GET.get('tecnico', '')
    fecha_inicio_str = request.GET.get('fecha_inicio', '')
    fecha_fin_str = request.GET.get('fecha_fin', '')
    
    # Solo mostrar reclamos de proyectos de su constructora
    reclamos = Reclamo.objects.filter(proyecto__in=proyectos_constructora).select_related('propietario', 'proyecto')
    
    if estado:
        reclamos = reclamos.filter(estado=estado)
    
    if busqueda:
        reclamos = reclamos.filter(
            Q(numero_folio__icontains=busqueda) |
            Q(propietario__nombre__icontains=busqueda) |
            Q(propietario__email__icontains=busqueda)
        )
    
    if proyecto_id:
        # Validar que el proyecto pertenece a su constructora
        proyecto = proyectos_constructora.filter(id=proyecto_id).first()
        if proyecto:
            reclamos = reclamos.filter(proyecto_id=proyecto_id)
    
    if especialidad_id:
        reclamos = reclamos.filter(categoria_id=especialidad_id)
    
    if tecnico_id:
        reclamos = reclamos.filter(tecnico_asignado_id=tecnico_id)

    # Filtro por rango de fechas (fecha_ingreso)
    # Acepta `YYYY-MM-DD` y aplica día completo para fin
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            fecha_inicio = timezone.make_aware(datetime.combine(fecha_inicio.date(), datetime.min.time()))
            reclamos = reclamos.filter(fecha_ingreso__gte=fecha_inicio)
        except ValueError:
            pass
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
            # fin del día
            fecha_fin_dt = timezone.make_aware(datetime.combine(fecha_fin.date(), datetime.max.time()))
            reclamos = reclamos.filter(fecha_ingreso__lte=fecha_fin_dt)
        except ValueError:
            pass
    
    reclamos = reclamos.order_by('-fecha_ingreso')
    
    # Obtener todas las especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los técnicos de la constructora
    tecnicos = Tecnico.objects.filter(constructora=constructora).order_by('nombre')
    
    context = {
        'reclamos': reclamos,
        'estado_filtro': estado,
        'busqueda': busqueda,
        'proyecto_filtro': proyecto_id,
        'especialidad_filtro': especialidad_id,
        'tecnico_filtro': tecnico_id,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'proyectos': proyectos_constructora,
        'especialidades': especialidades,
        'tecnicos': tecnicos,
        'constructora': constructora,
    }
    
    return render(request, 'admin/reclamos.html', context)


@login_required
def admin_detalle_reclamo(request, reclamo_id):
    """Ver detalle de un reclamo"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    citas = Cita.objects.filter(id_reclamo=reclamo).order_by('-fecha_programada')
    archivos = ArchivoEvidencia.objects.filter(id_reclamo=reclamo)
    
    context = {
        'reclamo': reclamo,
        'citas': citas,
        'archivos': archivos,
    }
    
    return render(request, 'admin/detalle_reclamo.html', context)


@login_required
def admin_usuarios(request):
    """Gestionar usuarios del sistema"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    from django.contrib.auth.models import User
    from .models import Perfil
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    # El administrador solo ve usuarios de su proyecto específico
    proyecto_admin = admin_perfil.proyecto
    
    # Filtros
    rol = request.GET.get('rol', '')
    busqueda = request.GET.get('q', '')
    
    usuarios_data = []
    
    # 1. Usuarios con Perfil (Supervisores, Administradores) del proyecto específico
    if not rol or rol in ['administrador', 'supervisor']:
        usuarios_perfil = User.objects.filter(
            perfil__proyecto=proyecto_admin
        ).distinct()
        
        if busqueda:
            usuarios_perfil = usuarios_perfil.filter(
                Q(username__icontains=busqueda) |
                Q(email__icontains=busqueda) |
                Q(first_name__icontains=busqueda)
            )
        
        for user in usuarios_perfil:
            perfil = Perfil.objects.filter(user=user).first()
            
            if rol and perfil and perfil.rol != rol:
                continue
            
            usuarios_data.append({
                'user': user,
                'perfil': perfil,
                'tipo': 'Perfil',
                'rol_display': perfil.rol if perfil else 'N/A'
            })
    
    # 2. Técnicos de la constructora (todos los técnicos de la constructora pueden trabajar en este proyecto)
    if not rol or rol == 'tecnico':
        tecnicos = Tecnico.objects.filter(constructora=constructora)
        
        if busqueda:
            tecnicos = tecnicos.filter(
                Q(nombre__icontains=busqueda) |
                Q(rut__icontains=busqueda) |
                Q(user__email__icontains=busqueda)
            )
        
        for tecnico in tecnicos:
            usuarios_data.append({
                'user': tecnico.user,
                'tecnico': tecnico,
                'tipo': 'Tecnico',
                'rol_display': 'Técnico'
            })
    
    # 3. Propietarios del proyecto específico
    if not rol or rol == 'propietario':
        propietarios = Propietario.objects.filter(proyecto=proyecto_admin)
        
        if busqueda:
            propietarios = propietarios.filter(
                Q(nombre__icontains=busqueda) |
                Q(rut__icontains=busqueda) |
                Q(email__icontains=busqueda)
            )
        
        for propietario in propietarios:
            usuarios_data.append({
                'user': propietario.user,
                'propietario': propietario,
                'tipo': 'Propietario',
                'rol_display': 'Propietario'
            })
    
    context = {
        'usuarios_data': usuarios_data,
        'rol_filtro': rol,
        'busqueda': busqueda,
        'constructora': constructora,
        'proyecto': proyecto_admin,
    }
    
    return render(request, 'admin/usuarios.html', context)


@login_required
def admin_detalle_usuario(request, usuario_id):
    """Ver detalle de un usuario"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    # Obtener el usuario
    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('admin_usuarios')
    
    # Preparar datos del usuario
    datos_usuario = {
        'usuario': usuario,
        'perfil': None,
        'tecnico': None,
        'propietario': None,
        'tipo': 'desconocido'
    }
    
    # 1. Verificar si es un Perfil (Supervisor/Administrador)
    perfil = Perfil.objects.filter(user=usuario).first()
    if perfil and perfil.proyecto and perfil.proyecto.constructora == constructora:
        datos_usuario['perfil'] = perfil
        datos_usuario['tipo'] = perfil.rol
        datos_usuario['proyecto'] = perfil.proyecto
    else:
        # 2. Verificar si es un Técnico
        try:
            tecnico = Tecnico.objects.get(user=usuario)
            if tecnico.constructora == constructora:
                datos_usuario['tecnico'] = tecnico
                datos_usuario['tipo'] = 'tecnico'
        except Tecnico.DoesNotExist:
            # 3. Verificar si es un Propietario
            try:
                propietario = Propietario.objects.get(user=usuario)
                if propietario.proyecto and propietario.proyecto.constructora == constructora:
                    datos_usuario['propietario'] = propietario
                    datos_usuario['tipo'] = 'propietario'
                    datos_usuario['proyecto'] = propietario.proyecto
            except Propietario.DoesNotExist:
                pass
    
    # Verificar permisos
    if datos_usuario['tipo'] == 'desconocido':
        messages.error(request, 'No tienes permiso para ver este usuario.')
        return redirect('admin_usuarios')
    
    context = {
        'datos_usuario': datos_usuario,
    }
    
    return render(request, 'admin/detalle_usuario.html', context)

@login_required
def admin_tecnicos(request):
    """Gestionar técnicos del sistema"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    
    # Solo mostrar técnicos de su constructora
    tecnicos = Tecnico.objects.filter(constructora=constructora).select_related('especialidad', 'constructora')
    
    context = {
        'tecnicos': tecnicos,
        'constructora': constructora,
    }
    
    return render(request, 'admin/tecnicos.html', context)


@login_required
@login_required
def admin_reportes(request):
    """Dashboard de KPIs - Visualización completa de los 15 KPIs para administrador"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    # Verificar si hay un proyecto específico seleccionado
    proyecto_id = request.GET.get('proyecto_id')
    proyecto_seleccionado = None
    
    if proyecto_id:
        proyecto_seleccionado = proyectos_constructora.filter(id=proyecto_id).first()
    
    # Obtener filtros de fecha (opcional)
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    fecha_inicio = None
    fecha_fin = None
    
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except:
            pass
    
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Determinar qué proyecto usar
    if proyecto_seleccionado:
        proyecto_para_kpi = proyecto_seleccionado
    else:
        # Si no hay proyecto seleccionado, usar el primero de la constructora
        proyecto_para_kpi = proyectos_constructora.first()
    
    # Obtener todos los KPIs del proyecto seleccionado
    kpis_data = KPICalculator.obtener_todos_los_kpis(proyecto_para_kpi, fecha_inicio, fecha_fin)
    
    # Mapeo de nombres descriptivos y categorías (igual al supervisor)
    kpi_info = {
        "KPI_01": {
            "nombre": "Tasa Reclamos Atendidos en Plazo",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de reclamos atendidos dentro del plazo comprometido"
        },
        "KPI_02": {
            "nombre": "Ratio Demanda vs Capacidad",
            "categoria": "Capacidad",
            "descripcion": "Relación entre demanda y capacidad de técnicos (overbooking)"
        },
        "KPI_03": {
            "nombre": "Tiempo Promedio Resolución",
            "categoria": "Eficiencia",
            "descripcion": "TTR: Tiempo promedio para resolver un reclamo"
        },
        "KPI_04": {
            "nombre": "Cumplimiento de Citas",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de citas programadas que se cumplen"
        },
        "KPI_05": {
            "nombre": "Casos Cerrados en Primera Visita",
            "categoria": "Eficiencia",
            "descripcion": "Porcentaje de reclamos resueltos en la primera visita"
        },
        "KPI_06": {
            "nombre": "Tasa Reaperturas",
            "categoria": "Calidad",
            "descripcion": "Porcentaje de reclamos que se reabren después de cerrados"
        },
        "KPI_07": {
            "nombre": "Costo Promedio por Reclamo",
            "categoria": "Costo",
            "descripcion": "Costo total invertido por reclamo"
        },
        "KPI_08": {
            "nombre": "Costo Materiales por Caso",
            "categoria": "Costo",
            "descripcion": "Costo de materiales utilizados por caso"
        },
        "KPI_09": {
            "nombre": "Índice Frecuencia Tipos Falla",
            "categoria": "Análisis",
            "descripcion": "Distribución de tipos de falla más comunes"
        },
        "KPI_10": {
            "nombre": "Puntualidad del Técnico",
            "categoria": "Cumplimiento",
            "descripcion": "Porcentaje de citas donde el técnico llega a tiempo"
        },
        "KPI_11": {
            "nombre": "Productividad Técnico",
            "categoria": "Productividad",
            "descripcion": "Promedio de reclamos resueltos por técnico"
        },
        "KPI_12": {
            "nombre": "Estado de Reclamos",
            "categoria": "Análisis",
            "descripcion": "Reclamos pendientes y resueltos"
        },
        "KPI_13": {
            "nombre": "Tiempo Cierre Documental",
            "categoria": "Eficiencia",
            "descripcion": "Tiempo para completar la documentación del reclamo"
        },
        "KPI_14": {
            "nombre": "Satisfacción del Cliente",
            "categoria": "Satisfacción",
            "descripcion": "Porcentaje de clientes satisfechos por proyecto"
        },
        "KPI_15": {
            "nombre": "Costo Reprocesos",
            "categoria": "Costo",
            "descripcion": "Porcentaje de costo invertido en reprocesos"
        }
    }
    
    # Construir lista de KPIs con información completa
    kpis_formateados = []
    
    for kpi_id in ["KPI_01", "KPI_02", "KPI_03", "KPI_04", "KPI_05", 
                   "KPI_06", "KPI_07", "KPI_08", "KPI_09", "KPI_10",
                   "KPI_11", "KPI_12", "KPI_13", "KPI_14", "KPI_15"]:
        
        kpi_data = kpis_data.get(kpi_id, {})
        info = kpi_info.get(kpi_id, {})
        
        valor = kpi_data.get('valor', None)
        unidad = kpi_data.get('unidad', '')
        
        # Casos especiales de KPIs con estructura compleja
        datos_adicionales = {k: v for k, v in kpi_data.items() if k not in ['valor', 'unidad']}
        
        # Para KPI_09, si tiene categorias pero no valor, usar el porcentaje más alto
        if kpi_id == 'KPI_09' and 'categorias' in kpi_data and valor is None:
            categorias = kpi_data.get('categorias', [])
            if categorias:
                valor = max([c.get('porcentaje', 0) for c in categorias]) if categorias else None
        
        # Para KPI_11, si tiene tecnicos pero no valor, calcular promedio
        if kpi_id == 'KPI_11' and 'tecnicos' in kpi_data and valor is None:
            tecnicos = kpi_data.get('tecnicos', [])
            if tecnicos:
                total_reclamos = sum([t.get('reclamos', 0) for t in tecnicos])
                promedio = total_reclamos / len(tecnicos) if tecnicos else 0
                valor = round(promedio, 2)
                unidad = 'reclamos/técnico'
        
        # Para KPI_12, si tiene reclamos pero no valor, usar el conteo
        if kpi_id == 'KPI_12' and valor is None and 'valor' not in kpi_data:
            if 'pendientes' in kpi_data:
                valor = kpi_data.get('pendientes', 0)
                unidad = 'reclamos'
        
        # Para KPI_14, si tiene satisfaccion pero no valor, calcular promedio
        if kpi_id == 'KPI_14' and valor is None and 'satisfaccion_promedio' in kpi_data:
            valor = kpi_data.get('satisfaccion_promedio')
            unidad = '/5.0'
        
        kpis_formateados.append({
            'id': kpi_id,
            'nombre': info.get('nombre', kpi_id),
            'categoria': info.get('categoria', 'Otros'),
            'descripcion': info.get('descripcion', ''),
            'valor': valor,
            'unidad': unidad,
            'datos_adicionales': datos_adicionales
        })
    
    # Agrupar por categoría
    kpis_por_categoria = {}
    for kpi in kpis_formateados:
        cat = kpi['categoria']
        if cat not in kpis_por_categoria:
            kpis_por_categoria[cat] = []
        kpis_por_categoria[cat].append(kpi)
    
    # Formatear fechas a DD/MM/YYYY para mostrar en el template
    fecha_inicio_display = fecha_inicio.strftime('%d/%m/%Y') if fecha_inicio else None
    fecha_fin_display = fecha_fin.strftime('%d/%m/%Y') if fecha_fin else None
    
    # Calcular tendencia mensual (igual a supervisor) usando proyecto_para_kpi
    try:
        base_date = None
        if fecha_inicio and fecha_fin and fecha_inicio.year == fecha_fin.year and fecha_inicio.month == fecha_fin.month:
            base_date = fecha_inicio
        elif fecha_inicio:
            base_date = fecha_inicio
        else:
            base_date = date.today()

        primer_dia_mes = date(base_date.year, base_date.month, 1)
        tendencia_mensual = Reclamo.objects.filter(
            proyecto=proyecto_para_kpi,
            fecha_ingreso__gte=timezone.make_aware(datetime.combine(primer_dia_mes, datetime.min.time())),
            estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado']
        ).exclude(estado='cancelado').annotate(
            fecha=TruncDate('fecha_ingreso')
        ).values('fecha').annotate(count=Count('id_reclamo')).order_by('fecha')

        dias_en_mes = calendar.monthrange(primer_dia_mes.year, primer_dia_mes.month)[1]
        datos_mes = {date(primer_dia_mes.year, primer_dia_mes.month, d): 0 for d in range(1, dias_en_mes + 1)}
        for item in tendencia_mensual:
            if item['fecha'] in datos_mes:
                datos_mes[item['fecha']] = item['count']

        labels_tendencia = [str(d) for d in range(1, dias_en_mes + 1)]
        valores_tendencia = [datos_mes.get(date(primer_dia_mes.year, primer_dia_mes.month, d), 0) for d in range(1, dias_en_mes + 1)]
    except Exception:
        labels_tendencia = []
        valores_tendencia = []

    context = {
        'constructora': constructora,
        'kpis': kpis_formateados,
        'kpis_por_categoria': kpis_por_categoria,
        'fecha_inicio': fecha_inicio_display,
        'fecha_fin': fecha_fin_display,
        'fecha_inicio_input': fecha_inicio_str,
        'fecha_fin_input': fecha_fin_str,
        'categorias': list(kpis_por_categoria.keys()),
        'proyectos_constructora': proyectos_constructora,
        'proyecto_seleccionado': proyecto_seleccionado,
        'labels_tendencia': labels_tendencia,
        'valores_tendencia': valores_tendencia,
    }
    
    return render(request, 'admin/reportes.html', context)



@login_required
def admin_costos(request):
    """Ver costos, materiales y stock de bodega"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    # Obtener todos los usos de materiales de sus proyectos
    from .models import UsoMaterial, Material
    
    usos = UsoMaterial.objects.filter(
        id_visita__id_reclamo__proyecto__in=proyectos_constructora
    ).select_related('id_visita', 'id_material').order_by('-fecha_uso')
    
    # Obtener stock de bodega
    materiales = Material.objects.all().order_by('nombre')
    
    # Calcular costo total del stock
    costo_total_stock = sum([
        (m.stock_actual or 0) * m.costo_unitario for m in materiales
    ])
    
    # Calcular costo de materiales usados
    costo_total_usado = sum([
        (uso.id_material.costo_unitario * uso.cantidad_usada) for uso in usos if uso.id_material and uso.cantidad_usada
    ])
    
    context = {
        'usos': usos,
        'materiales': materiales,
        'constructora': constructora,
        'costo_total_stock': costo_total_stock,
        'costo_total_usado': costo_total_usado,
    }
    
    return render(request, 'admin/costos.html', context)



@login_required
def export_kpis_csv(request):
    """
    Vista que exporta todos los KPIs en CSV para importar en Power BI.
    """
    supervisor = get_supervisor_from_user(request.user)
    if not supervisor:
        messages.error(request, 'No autorizado')
        return redirect('login')
    
    proyecto = supervisor.proyecto
    
    # Obtener KPIs
    kpis = KPICalculator.obtener_todos_los_kpis(proyecto)
    
    # Crear CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="kpis_powerbi.csv"'
    
    writer = csv.writer(response)
    
    # Encabezado
    writer.writerow(['KPI_ID', 'KPI_Nombre', 'Valor', 'Unidad', 'Descripcion', 'Fecha_Generacion'])
    
    timestamp = timezone.now().isoformat()
    
    # KPIs simples
    simple_kpis = [
        ('01', 'Tasa Reclamos Atendidos en Plazo', kpis.get('KPI_01_Tasa_Reclamos_Atendidos', {})),
        ('02', 'Ratio Demanda vs Capacidad', kpis.get('KPI_02_Ratio_Demanda_Capacidad', {})),
        ('03', 'Tiempo Promedio de Resolucion (TTR)', kpis.get('KPI_03_TTR', {})),
        ('04', 'Cumplimiento de Citas', kpis.get('KPI_04_Cumplimiento_Citas', {})),
        ('05', 'Casos Cerrados en Primera Visita', kpis.get('KPI_05_Casos_Primera_Visita', {})),
        ('06', 'Tasa de Reaperturas', kpis.get('KPI_06_Tasa_Reaperturas', {})),
        ('07', 'Costo Promedio por Reclamo', kpis.get('KPI_07_Costo_Promedio_Reclamo', {})),
        ('08', 'Costo Materiales por Caso', kpis.get('KPI_08_Costo_Materiales_Caso', {})),
        ('10', 'Puntualidad Tecnico', kpis.get('KPI_10_Puntualidad_Tecnico', {})),
        ('13', 'Tiempo Cierre Documental', kpis.get('KPI_13_Cierre_Documental', {})),
        ('15', 'Costo de Reprocesos', kpis.get('KPI_15_Costo_Reprocesos', {})),
    ]
    
    for kpi_id, kpi_nombre, kpi_data in simple_kpis:
        valor = kpi_data.get('valor', 'N/A')
        unidad = kpi_data.get('unidad', '')
        descripcion = kpi_data.get('descripcion', '')
        writer.writerow([kpi_id, kpi_nombre, valor, unidad, descripcion, timestamp])
    
    return response


@login_required
def admin_crear_supervisor(request):
    """Crear un nuevo supervisor"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    proyectos_constructora = Proyecto.objects.filter(constructora=constructora)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        rut = request.POST.get('rut')
        telefono = request.POST.get('telefono')
        proyecto_id = request.POST.get('proyecto')
        password = request.POST.get('password')
        
        # Validaciones
        if not all([username, email, nombre, proyecto_id, password]):
            messages.error(request, 'Completa todos los campos requeridos.')
            return redirect('admin_crear_supervisor')
        
        # Validar que el proyecto pertenece a su constructora
        proyecto = proyectos_constructora.filter(id=proyecto_id).first()
        if not proyecto:
            messages.error(request, 'Proyecto no válido.')
            return redirect('admin_crear_supervisor')
        
        # Validar usuario único
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
            return redirect('admin_crear_supervisor')
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido or ''
        )
        
        # Crear perfil
        Perfil.objects.create(
            user=user,
            rol='supervisor',
            rut=rut or '',
            telefono=telefono or '',
            proyecto=proyecto,
            direccion=''
        )
        
        messages.success(request, f'Supervisor {nombre} creado exitosamente.')
        return redirect('admin_usuarios')
    
    context = {
        'proyectos': proyectos_constructora,
        'constructora': constructora,
    }
    
    return render(request, 'admin/crear_supervisor.html', context)


@login_required
def admin_eliminar_supervisor(request, supervisor_id):
    """Eliminar un supervisor"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    
    # Obtener el supervisor por su usuario
    try:
        supervisor_user = User.objects.get(id=supervisor_id)
        perfil_supervisor = Perfil.objects.get(user=supervisor_user, rol='supervisor', proyecto__constructora=constructora)
    except (User.DoesNotExist, Perfil.DoesNotExist):
        messages.error(request, 'Supervisor no encontrado.')
        return redirect('admin_usuarios')
    
    if request.method == 'POST':
        nombre_supervisor = supervisor_user.first_name or supervisor_user.username
        
        # Eliminar perfil
        perfil_supervisor.delete()
        
        # Eliminar usuario
        supervisor_user.delete()
        
        messages.success(request, f'Supervisor {nombre_supervisor} eliminado exitosamente.')
        return redirect('admin_usuarios')
    
    context = {
        'supervisor': supervisor_user,
        'perfil': perfil_supervisor,
    }
    
    return render(request, 'admin/confirmar_eliminar_supervisor.html', context)


@login_required
def admin_crear_tecnico(request):
    """Crear un nuevo técnico"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        rut = request.POST.get('rut')
        especialidad_id = request.POST.get('especialidad')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        zona_cobertura = request.POST.get('zona_cobertura')
        password = request.POST.get('password')
        
        # Validaciones
        if not all([nombre, rut, especialidad_id, password]):
            messages.error(request, 'Completa todos los campos requeridos.')
            return redirect('admin_crear_tecnico')
        
        # Validar especialidad existe
        especialidad = Especialidad.objects.filter(id=especialidad_id).first()
        if not especialidad:
            messages.error(request, 'Especialidad no válida.')
            return redirect('admin_crear_tecnico')
        
        # Validar usuario único
        username = f"tecnico_{rut.replace('.', '').replace('-', '')}"
        if User.objects.filter(username=username).exists():
            username = f"{username}_{Tecnico.objects.count()}"
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@constructora.local",
            password=password,
            first_name=nombre
        )
        
        # Crear técnico
        Tecnico.objects.create(
            rut=rut,
            nombre=nombre,
            especialidad=especialidad,
            constructora=constructora,
            user=user,
            telefono=telefono or '',
            email=email or '',
            zona_cobertura=zona_cobertura or '',
            estado='activo'
        )
        
        messages.success(request, f'Técnico {nombre} creado exitosamente.')
        return redirect('admin_tecnicos')
    
    especialidades = Especialidad.objects.all()
    
    context = {
        'especialidades': especialidades,
        'constructora': constructora,
    }
    
    return render(request, 'admin/crear_tecnico.html', context)


@login_required
def admin_editar_tecnico(request, tecnico_id):
    """Editar un técnico existente"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    
    # Obtener el técnico
    tecnico = get_object_or_404(Tecnico, id_tecnico=tecnico_id, constructora=constructora)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        especialidad_id = request.POST.get('especialidad')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        zona_cobertura = request.POST.get('zona_cobertura')
        estado = request.POST.get('estado')
        
        # Validaciones
        if not all([nombre, especialidad_id]):
            messages.error(request, 'Completa los campos requeridos.')
            return redirect('admin_editar_tecnico', tecnico_id=tecnico_id)
        
        # Validar especialidad existe
        especialidad = Especialidad.objects.filter(id=especialidad_id).first()
        if not especialidad:
            messages.error(request, 'Especialidad no válida.')
            return redirect('admin_editar_tecnico', tecnico_id=tecnico_id)
        
        # Actualizar técnico
        tecnico.nombre = nombre
        tecnico.especialidad = especialidad
        tecnico.telefono = telefono or ''
        tecnico.email = email or ''
        tecnico.zona_cobertura = zona_cobertura or ''
        tecnico.estado = estado or 'activo'
        tecnico.save()
        
        # Actualizar usuario
        if tecnico.user:
            tecnico.user.first_name = nombre
            tecnico.user.email = email or tecnico.user.email
            tecnico.user.save()
        
        messages.success(request, f'Técnico {nombre} actualizado exitosamente.')
        return redirect('admin_tecnicos')
    
    especialidades = Especialidad.objects.all()
    
    context = {
        'tecnico': tecnico,
        'especialidades': especialidades,
        'constructora': constructora,
    }
    
    return render(request, 'admin/editar_tecnico.html', context)


@login_required
def admin_eliminar_tecnico(request, tecnico_id):
    """Eliminar un técnico"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_reclamos')
    
    # Obtener perfil y constructora del admin
    admin_perfil = Perfil.objects.filter(user=request.user, rol='administrador').first()
    if not admin_perfil or not admin_perfil.proyecto:
        messages.error(request, 'No tienes un proyecto asignado.')
        return redirect('mis_reclamos')
    
    constructora = admin_perfil.proyecto.constructora
    
    # Obtener el técnico
    tecnico = get_object_or_404(Tecnico, id_tecnico=tecnico_id, constructora=constructora)
    
    if request.method == 'POST':
        nombre_tecnico = tecnico.nombre
        user_id = tecnico.user.id if tecnico.user else None
        
        # Eliminar técnico
        tecnico.delete()
        
        # Eliminar usuario del sistema si existe
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.delete()
            except User.DoesNotExist:
                pass
        
        messages.success(request, f'Técnico {nombre_tecnico} eliminado exitosamente.')
        return redirect('admin_tecnicos')
    
    context = {
        'tecnico': tecnico,
    }
    
    return render(request, 'admin/confirmar_eliminar_tecnico.html', context)

