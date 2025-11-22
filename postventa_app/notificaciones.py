"""
Sistema de notificaciones por email.
Plantillas centralizadas para todos los mensajes de notificación.
"""
from django.utils import timezone


class EmailTemplates:
    """
    Clase con todas las plantillas de email del sistema.
    Centraliza todos los mensajes para fácil edición y mantenimiento.
    """
    
    # ========================================
    # NOTIFICACIONES PARA PROPIETARIOS
    # ========================================
    
    @staticmethod
    def reclamo_recibido_con_tecnico(propietario, reclamo, tecnico):
        """
        Email cuando se crea un reclamo y se asigna técnico inmediatamente.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            tecnico: Objeto Tecnico
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        
        asunto = f"Reclamo {reclamo.folio} Recibido - Técnico Asignado"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Su reclamo {reclamo.folio} ha sido recibido y procesado exitosamente en nuestro sistema.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Ubicación: {reclamo.ubicacion_especifica}
- Descripción: {reclamo.descripcion[:100]}{'...' if len(reclamo.descripcion) > 100 else ''}

TÉCNICO ASIGNADO:
- Nombre: {tecnico_nombre}
- Especialidad: {reclamo.categoria.nombre}

Su cita esta programada.

Puede hacer seguimiento del estado de su reclamo ingresando a la plataforma con sus credenciales.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def reclamo_recibido_sin_tecnico(propietario, reclamo):
        """
        Email cuando se crea un reclamo pero aún no se asigna técnico.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        asunto = f"Reclamo {reclamo.folio} Recibido - En Proceso de Asignación"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Su reclamo {reclamo.folio} ha sido recibido exitosamente en nuestro sistema.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Ubicación: {reclamo.ubicacion_especifica}

Pronto un técnico especializado será asignado para atender su solicitud. Le notificaremos cuando esto ocurra.

Puede hacer seguimiento del estado de su reclamo ingresando a la plataforma.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def tecnico_asignado(propietario, reclamo, tecnico):
        """
        Email cuando se asigna un técnico a un reclamo existente.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            tecnico: Objeto Tecnico
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        
        asunto = f"Técnico Asignado a su Reclamo {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Le informamos que se ha asignado un técnico especializado a su reclamo {reclamo.folio}.

TÉCNICO ASIGNADO:
- Nombre: {tecnico_nombre}
- Especialidad: {reclamo.categoria.nombre}

El técnico se pondrá en contacto con usted para coordinar una visita. Puede revisar los detalles completos y el estado de su reclamo ingresando a la plataforma.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def cita_confirmada(propietario, reclamo, cita):
        """
        Email cuando se confirma una cita con el técnico.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            cita: Objeto Cita
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = cita.tecnico.usuario.get_full_name() or cita.tecnico.usuario.username
        fecha_cita = cita.fecha_cita.strftime('%d/%m/%Y')
        hora_cita = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
        
        asunto = f"Cita Confirmada - Visita Técnico para Reclamo {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Su cita para el reclamo {reclamo.folio} ha sido confirmada.

DETALLES DE LA CITA:
- Fecha: {fecha_cita}
- Hora: {hora_cita}
- Técnico: {tecnico_nombre}
- Categoría: {reclamo.categoria.nombre}
- Ubicación: {reclamo.ubicacion_especifica}

Por favor, esté disponible en el horario acordado y asegúrese de que el técnico pueda acceder al área afectada.

Si necesita reprogramar, puede hacerlo desde la plataforma.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def cita_reprogramada_propietario(propietario, reclamo, cita, fecha_anterior):
        """
        Email cuando se reprograma una cita (notificación al propietario).
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            cita: Objeto Cita con nueva fecha
            fecha_anterior: datetime con la fecha anterior
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = cita.tecnico.usuario.get_full_name() or cita.tecnico.usuario.username
        fecha_nueva = cita.fecha_cita.strftime('%d/%m/%Y')
        hora_nueva = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
        fecha_ant = fecha_anterior.strftime('%d/%m/%Y')
        
        asunto = f"Cita Reprogramada - Reclamo {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Le informamos que su cita para el reclamo {reclamo.folio} ha sido reprogramada.

FECHA ANTERIOR:
- {fecha_ant}

NUEVA FECHA Y HORA:
- Fecha: {fecha_nueva}
- Hora: {hora_nueva}
- Técnico: {tecnico_nombre}

Por favor tome nota del nuevo horario. Si tiene alguna dificultad con esta fecha, puede contactarnos o reprogramar desde la plataforma.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def reclamo_en_proceso(propietario, reclamo, tecnico):
        """
        Email cuando el técnico inicia el trabajo en el reclamo.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            tecnico: Objeto Tecnico
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        
        asunto = f"Reclamo {reclamo.folio} En Proceso"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Le informamos que el técnico {tecnico_nombre} ha iniciado el trabajo en su reclamo {reclamo.folio}.

El técnico está trabajando en la resolución del problema. Puede hacer seguimiento del progreso ingresando a la plataforma.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def reclamo_resuelto(propietario, reclamo, tecnico):
        """
        Email cuando se marca un reclamo como resuelto.
        
        Args:
            propietario: Objeto Propietario
            reclamo: Objeto Reclamo
            tecnico: Objeto Tecnico
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        
        asunto = f"Reclamo {reclamo.folio} Resuelto - Solicitud de Calificación"
        
        mensaje = f"""Estimado(a) {propietario.nombre},

Nos complace informarle que su reclamo {reclamo.folio} ha sido marcado como resuelto.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Técnico: {tecnico_nombre}
- Estado: Resuelto

Le agradeceremos que califique el servicio recibido ingresando a la plataforma. Su opinión es muy importante para nosotros y nos ayuda a mejorar continuamente.

Si el problema persiste o tiene alguna observación, por favor no dude en contactarnos.

Saludos cordiales,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    # ========================================
    # NOTIFICACIONES PARA TÉCNICOS
    # ========================================
    
    @staticmethod
    def nuevo_reclamo_asignado(tecnico, reclamo):
        """
        Email cuando se asigna un nuevo reclamo a un técnico.
        
        Args:
            tecnico: Objeto Tecnico
            reclamo: Objeto Reclamo
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        propietario_nombre = reclamo.propietario.nombre if reclamo.propietario else 'No especificado'
        propietario_telefono = reclamo.propietario.telefono if reclamo.propietario else 'N/A'
        propietario_unidad = reclamo.propietario.unidad if reclamo.propietario else 'N/A'
        
        asunto = f"Nuevo Reclamo Asignado: {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {tecnico_nombre},

Se le ha asignado un nuevo reclamo que requiere su atención.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Propietario: {propietario_nombre}
- Proyecto: {reclamo.proyecto.nombre}
- Unidad: {propietario_unidad}
- Ubicación: {reclamo.ubicacion_especifica}
- Descripción: {reclamo.descripcion[:150]}{'...' if len(reclamo.descripcion) > 150 else ''}

CONTACTO DEL PROPIETARIO:
- Teléfono: {propietario_telefono}

Por favor, revise los detalles completos en su panel y coordine la visita con el propietario a la brevedad.

Saludos,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def recordatorio_visita(tecnico, cita):
        """
        Email recordatorio de visita para el día de hoy.
        
        Args:
            tecnico: Objeto Tecnico
            cita: Objeto Cita
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        propietario_nombre = cita.reclamo.propietario.nombre if cita.reclamo.propietario else 'No especificado'
        propietario_telefono = cita.reclamo.propietario.telefono if cita.reclamo.propietario else 'N/A'
        hora_cita = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
        
        asunto = f"Recordatorio de Visita - Hoy a las {hora_cita}"
        
        mensaje = f"""Estimado(a) {tecnico_nombre},

Este es un recordatorio de que tiene una visita programada para el día de hoy.

DETALLES DE LA CITA:
- Hora: {hora_cita}
- Reclamo: {cita.reclamo.folio}
- Categoría: {cita.reclamo.categoria.nombre}
- Propietario: {propietario_nombre}
- Teléfono: {propietario_telefono}
- Ubicación: {cita.reclamo.ubicacion_especifica}

Por favor revise su agenda y confirme que cuenta con los materiales y herramientas necesarios para realizar el trabajo.

Saludos,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def cita_reprogramada_tecnico(tecnico, reclamo, cita, fecha_anterior):
        """
        Email cuando se reprograma una cita (notificación al técnico).
        
        Args:
            tecnico: Objeto Tecnico
            reclamo: Objeto Reclamo
            cita: Objeto Cita con nueva fecha
            fecha_anterior: datetime con la fecha anterior
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        propietario_nombre = reclamo.propietario.nombre if reclamo.propietario else 'N/A'
        fecha_nueva = cita.fecha_cita.strftime('%d/%m/%Y')
        hora_nueva = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
        
        asunto = f"Cita Reprogramada - Reclamo {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {tecnico_nombre},

Una de sus citas ha sido reprogramada.

NUEVA INFORMACIÓN:
- Reclamo: {reclamo.folio}
- Nueva fecha: {fecha_nueva}
- Nueva hora: {hora_nueva}
- Propietario: {propietario_nombre}
- Ubicación: {reclamo.ubicacion_especifica}

Por favor verifique su calendario actualizado en la plataforma y coordine con el propietario si es necesario.

Saludos,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}
    
    @staticmethod
    def materiales_aprobados(tecnico, reclamo, materiales):
        """
        Email cuando se aprueban materiales solicitados.
        
        Args:
            tecnico: Objeto Tecnico
            reclamo: Objeto Reclamo
            materiales: Lista de objetos Material
        
        Returns:
            dict: {'asunto': str, 'mensaje': str}
        """
        tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
        
        lista_materiales = "\n".join([
            f"- {mat.nombre}: {mat.cantidad} {mat.unidad} (${mat.costo_unitario:,.0f} c/u)"
            for mat in materiales
        ])
        
        asunto = f"Materiales Aprobados - Reclamo {reclamo.folio}"
        
        mensaje = f"""Estimado(a) {tecnico_nombre},

Se han aprobado los materiales solicitados para el reclamo {reclamo.folio}.

MATERIALES APROBADOS:
{lista_materiales}

Puede proceder con la adquisición de estos materiales según los procedimientos establecidos.

Saludos,
Equipo de Postventa Pro"""
        
        return {'asunto': asunto, 'mensaje': mensaje}


# ========================================
# FUNCIONES AUXILIARES PARA CREAR NOTIFICACIONES
# ========================================

def crear_notificacion_propietario(propietario, reclamo, tipo_notificacion, **kwargs):
    """
    Crea una notificación para un propietario.
    
    Args:
        propietario: Objeto Propietario
        reclamo: Objeto Reclamo
        tipo_notificacion: str con el tipo de notificación
        **kwargs: Argumentos adicionales según el tipo
    
    Returns:
        Notificacion: Objeto creado
    """
    from .models import Notificacion
    
    # Mapeo de tipos a métodos de plantilla
    plantillas = {
        'reclamo_recibido_con_tecnico': EmailTemplates.reclamo_recibido_con_tecnico,
        'reclamo_recibido_sin_tecnico': EmailTemplates.reclamo_recibido_sin_tecnico,
        'tecnico_asignado': EmailTemplates.tecnico_asignado,
        'cita_confirmada': EmailTemplates.cita_confirmada,
        'cita_reprogramada': EmailTemplates.cita_reprogramada_propietario,
        'reclamo_en_proceso': EmailTemplates.reclamo_en_proceso,
        'reclamo_resuelto': EmailTemplates.reclamo_resuelto,
    }
    
    if tipo_notificacion not in plantillas:
        raise ValueError(f"Tipo de notificación '{tipo_notificacion}' no válido")
    
    # Obtener plantilla
    plantilla = plantillas[tipo_notificacion]
    
    # Preparar argumentos según el tipo
    if tipo_notificacion in ['reclamo_recibido_con_tecnico', 'tecnico_asignado', 'reclamo_en_proceso', 'reclamo_resuelto']:
        email_data = plantilla(propietario, reclamo, kwargs['tecnico'])
    elif tipo_notificacion == 'reclamo_recibido_sin_tecnico':
        email_data = plantilla(propietario, reclamo)
    elif tipo_notificacion in ['cita_confirmada']:
        email_data = plantilla(propietario, reclamo, kwargs['cita'])
    elif tipo_notificacion == 'cita_reprogramada':
        email_data = plantilla(propietario, reclamo, kwargs['cita'], kwargs['fecha_anterior'])
    
    # Crear notificación
    notificacion = Notificacion.objects.create(
        propietario=propietario,
        reclamo=reclamo,
        cita=kwargs.get('cita'),
        asunto=email_data['asunto'],
        mensaje=email_data['mensaje'],
        estado='pendiente'
    )
    
    return notificacion


def crear_notificacion_tecnico(tecnico, reclamo, tipo_notificacion, **kwargs):
    """
    Crea una notificación para un técnico.
    
    Args:
        tecnico: Objeto Tecnico
        reclamo: Objeto Reclamo
        tipo_notificacion: str con el tipo de notificación
        **kwargs: Argumentos adicionales según el tipo
    
    Returns:
        Notificacion: Objeto creado
    """
    from .models import Notificacion
    
    # Mapeo de tipos a métodos de plantilla
    plantillas = {
        'nuevo_reclamo': EmailTemplates.nuevo_reclamo_asignado,
        'recordatorio_visita': EmailTemplates.recordatorio_visita,
        'cita_reprogramada': EmailTemplates.cita_reprogramada_tecnico,
        'materiales_aprobados': EmailTemplates.materiales_aprobados,
    }
    
    if tipo_notificacion not in plantillas:
        raise ValueError(f"Tipo de notificación '{tipo_notificacion}' no válido")
    
    # Obtener plantilla
    plantilla = plantillas[tipo_notificacion]
    
    # Preparar argumentos según el tipo
    if tipo_notificacion == 'nuevo_reclamo':
        email_data = plantilla(tecnico, reclamo)
    elif tipo_notificacion == 'recordatorio_visita':
        email_data = plantilla(tecnico, kwargs['cita'])
    elif tipo_notificacion == 'cita_reprogramada':
        email_data = plantilla(tecnico, reclamo, kwargs['cita'], kwargs['fecha_anterior'])
    elif tipo_notificacion == 'materiales_aprobados':
        email_data = plantilla(tecnico, reclamo, kwargs['materiales'])
    
    # Crear notificación
    notificacion = Notificacion.objects.create(
        tecnico=tecnico,
        reclamo=reclamo,
        cita=kwargs.get('cita'),
        asunto=email_data['asunto'],
        mensaje=email_data['mensaje'],
        estado='pendiente'
    )
    
    return notificacion
