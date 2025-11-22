"""
Management command para poblar datos de prueba en los nuevos modelos:
- Material
- Escombro  
- Notificacion
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from postventa_app.models import (
    Reclamo, Material, Escombro, Notificacion,
    Propietario, Tecnico, Cita
)


class Command(BaseCommand):
    help = 'Pobla datos de prueba para los modelos Material, Escombro y Notificacion'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando población de datos...'))
        
        # Obtener reclamos existentes
        reclamos = Reclamo.objects.all()
        if not reclamos.exists():
            self.stdout.write(self.style.ERROR('No hay reclamos en la base de datos. Ejecuta primero poblar_datos.'))
            return
        
        # Poblar Material
        self.stdout.write(self.style.SUCCESS('\n1. Poblando Materiales...'))
        materiales_creados = self.poblar_materiales(reclamos)
        
        # Poblar Escombro
        self.stdout.write(self.style.SUCCESS('\n2. Poblando Escombros...'))
        escombros_creados = self.poblar_escombros(reclamos)
        
        # Poblar Notificacion
        self.stdout.write(self.style.SUCCESS('\n3. Poblando Notificaciones...'))
        notificaciones_creadas = self.poblar_notificaciones()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Proceso completado:'))
        self.stdout.write(self.style.SUCCESS(f'   - {materiales_creados} materiales creados'))
        self.stdout.write(self.style.SUCCESS(f'   - {escombros_creados} escombros creados'))
        self.stdout.write(self.style.SUCCESS(f'   - {notificaciones_creadas} notificaciones creadas'))

    def poblar_materiales(self, reclamos):
        """Crea materiales de prueba asociados a reclamos"""
        materiales_data = [
            # Materiales comunes en postventa
            {'nombre': 'Cemento Portland', 'unidad': 'kg', 'costo_unitario': 5500, 'proveedor': 'Cemento Polpaico'},
            {'nombre': 'Pintura Látex Blanca', 'unidad': 'litro', 'costo_unitario': 12000, 'proveedor': 'Sherwin Williams'},
            {'nombre': 'Cerámica Piso', 'unidad': 'm2', 'costo_unitario': 8900, 'proveedor': 'Cerámicas Cordillera'},
            {'nombre': 'Adhesivo Cerámico', 'unidad': 'kg', 'costo_unitario': 6500, 'proveedor': 'MK'},
            {'nombre': 'Sellador Acrílico', 'unidad': 'litro', 'costo_unitario': 7800, 'proveedor': 'Sika'},
            {'nombre': 'Yeso Cartón 10mm', 'unidad': 'plancha', 'costo_unitario': 4200, 'proveedor': 'Volcán'},
            {'nombre': 'Perfil Metalico C', 'unidad': 'metro', 'costo_unitario': 2500, 'proveedor': 'Cintac'},
            {'nombre': 'Lana Mineral', 'unidad': 'm2', 'costo_unitario': 3200, 'proveedor': 'Volcán'},
            {'nombre': 'Enchufes Schuko', 'unidad': 'unidad', 'costo_unitario': 2800, 'proveedor': 'Schneider Electric'},
            {'nombre': 'Cable 2.5mm', 'unidad': 'metro', 'costo_unitario': 890, 'proveedor': 'Procobre'},
            {'nombre': 'Tubo PVC 50mm', 'unidad': 'metro', 'costo_unitario': 3500, 'proveedor': 'ViniLit'},
            {'nombre': 'Grifería Monomando', 'unidad': 'unidad', 'costo_unitario': 35000, 'proveedor': 'FV'},
        ]
        
        contador = 0
        # Seleccionar algunos reclamos que ya tengan estado != 'pendiente' (procesados)
        reclamos_procesados = reclamos.exclude(estado='pendiente')[:8]
        
        for i, reclamo in enumerate(reclamos_procesados):
            # Cada reclamo tendrá entre 1 y 3 materiales
            num_materiales = (i % 3) + 1
            
            for j in range(num_materiales):
                material_data = materiales_data[(i * 3 + j) % len(materiales_data)]
                
                cantidad = [1, 2, 3, 5, 10, 15][j % 6]
                
                Material.objects.create(
                    reclamo=reclamo,
                    nombre=material_data['nombre'],
                    cantidad=cantidad,
                    unidad=material_data['unidad'],
                    costo_unitario=material_data['costo_unitario'],
                    proveedor=material_data['proveedor'],
                    fecha_uso=timezone.now() - timedelta(days=i*2),
                    observaciones=f'Material utilizado en la resolución del reclamo {reclamo.folio}'
                )
                contador += 1
                self.stdout.write(f'   ✓ Material: {material_data["nombre"]} ({cantidad} {material_data["unidad"]}) → Reclamo {reclamo.folio}')
        
        return contador

    def poblar_escombros(self, reclamos):
        """Crea registros de escombros para reclamos que lo requieren"""
        tipos_escombro = [
            ('ceramica', 'Restos de cerámica y baldosas'),
            ('yeso', 'Placas de yeso cartón y estuco'),
            ('madera', 'Marcos de ventana y puertas'),
            ('mixto', 'Mezcla de materiales de construcción'),
            ('hormigon', 'Escombros de concreto y mortero'),
            ('electrico', 'Cables y conductos eléctricos'),
        ]
        
        estados = ['pendiente', 'programado', 'retirado']
        empresas = [
            'Retiro Escombros Express',
            'EcoRetiro Ltda',
            'Servicios Ambientales SA',
            'Retiros Industriales Chile'
        ]
        
        contador = 0
        # Migrar datos legacy: buscar reclamos con requiere_retiro_escombros=True
        reclamos_con_escombros = reclamos.filter(requiere_retiro_escombros=True)
        
        for i, reclamo in enumerate(reclamos_con_escombros[:6]):
            tipo_idx = i % len(tipos_escombro)
            tipo, obs = tipos_escombro[tipo_idx]
            estado = estados[i % len(estados)]
            
            # Determinar fechas según estado
            fecha_prog = None
            fecha_ret = None
            empresa = None
            costo = None
            
            if estado in ['programado', 'retirado']:
                fecha_prog = timezone.now() + timedelta(days=3 + i)
                empresa = empresas[i % len(empresas)]
                costo = 25000 + (i * 5000)
                
            if estado == 'retirado':
                fecha_ret = timezone.now() - timedelta(days=i)
            
            # Migrar datos legacy si existen
            if reclamo.estado_escombros:
                estado = reclamo.estado_escombros
            if reclamo.fecha_retiro_escombros:
                fecha_ret = reclamo.fecha_retiro_escombros
            
            Escombro.objects.create(
                reclamo=reclamo,
                requiere_retiro=True,
                volumen_estimado=0.5 + (i * 0.3),
                tipo_escombro=tipo,
                estado=estado,
                fecha_programada=fecha_prog,
                fecha_retiro=fecha_ret,
                empresa_retiro=empresa,
                costo_retiro=costo,
                observaciones=obs
            )
            contador += 1
            self.stdout.write(f'   ✓ Escombro: {tipo} ({estado}) → Reclamo {reclamo.folio}')
        
        return contador

    def poblar_notificaciones(self):
        """Crea notificaciones email de prueba para propietarios y técnicos"""
        propietarios = Propietario.objects.all()[:5]
        tecnicos = Tecnico.objects.all()[:3]
        reclamos = Reclamo.objects.all()[:5]
        citas = Cita.objects.all()[:3]
        
        estados = ['pendiente', 'enviada', 'leida']
        
        notificaciones_templates = [
            # Para propietarios
            {
                'tipo': 'reclamo_recibido',
                'asunto': 'Reclamo {folio} Recibido - Técnico Asignado',
                'destinatario': 'propietario'
            },
            {
                'tipo': 'tecnico_asignado',
                'asunto': 'Técnico Asignado a su Reclamo {folio}',
                'destinatario': 'propietario'
            },
            {
                'tipo': 'cita_confirmada',
                'asunto': 'Cita Confirmada - Visita Técnico',
                'destinatario': 'propietario'
            },
            {
                'tipo': 'reclamo_resuelto',
                'asunto': 'Reclamo {folio} Resuelto - Solicitud de Calificación',
                'destinatario': 'propietario'
            },
            # Para técnicos
            {
                'tipo': 'nuevo_reclamo',
                'asunto': 'Nuevo Reclamo Asignado: {folio}',
                'destinatario': 'tecnico'
            },
            {
                'tipo': 'recordatorio_visita',
                'asunto': 'Recordatorio de Visita - Hoy',
                'destinatario': 'tecnico'
            },
            {
                'tipo': 'cita_reprogramada',
                'asunto': 'Cita Reprogramada - Reclamo {folio}',
                'destinatario': 'tecnico'
            },
        ]
        
        contador = 0
        
        # Notificaciones para propietarios
        for i, template in enumerate([n for n in notificaciones_templates if n['destinatario'] == 'propietario']):
            if propietarios.exists() and reclamos.exists():
                propietario = propietarios[i % len(propietarios)]
                reclamo = reclamos[i % len(reclamos)]
                cita = citas[i % len(citas)] if citas.exists() else None
                estado = estados[i % len(estados)]
                
                # Determinar fechas según estado
                fecha_creacion = timezone.now() - timedelta(days=5-i)
                fecha_envio = None
                fecha_lectura = None
                
                if estado in ['enviada', 'leida']:
                    fecha_envio = fecha_creacion + timedelta(minutes=5)
                    
                if estado == 'leida':
                    fecha_lectura = fecha_envio + timedelta(hours=2)
                
                # Generar mensaje personalizado según tipo
                if template['tipo'] == 'reclamo_recibido':
                    if reclamo.tecnico_asignado:
                        tecnico_nombre = reclamo.tecnico_asignado.usuario.get_full_name() or reclamo.tecnico_asignado.usuario.username
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

El técnico se pondrá en contacto con usted próximamente para coordinar una visita.

Puede hacer seguimiento del estado de su reclamo ingresando a la plataforma con sus credenciales.

Saludos cordiales,
Equipo de Postventa"""
                    else:
                        mensaje = f"""Estimado(a) {propietario.nombre},

Su reclamo {reclamo.folio} ha sido recibido exitosamente en nuestro sistema.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Ubicación: {reclamo.ubicacion_especifica}

Pronto un técnico especializado será asignado para atender su solicitud. Le notificaremos cuando esto ocurra.

Puede hacer seguimiento del estado de su reclamo ingresando a la plataforma.

Saludos cordiales,
Equipo de Postventa"""
                
                elif template['tipo'] == 'tecnico_asignado':
                    if reclamo.tecnico_asignado:
                        tecnico_nombre = reclamo.tecnico_asignado.usuario.get_full_name() or reclamo.tecnico_asignado.usuario.username
                        mensaje = f"""Estimado(a) {propietario.nombre},

Le informamos que se ha asignado un técnico especializado a su reclamo {reclamo.folio}.

TÉCNICO ASIGNADO:
- Nombre: {tecnico_nombre}
- Especialidad: {reclamo.categoria.nombre}

El técnico se pondrá en contacto con usted para coordinar una visita. Puede revisar los detalles completos y el estado de su reclamo ingresando a la plataforma.

Saludos cordiales,
Equipo de Postventa"""
                    else:
                        mensaje = f"Estimado(a) {propietario.nombre},\n\nSe está procesando la asignación de un técnico a su reclamo {reclamo.folio}.\n\nSaludos cordiales,\nEquipo de Postventa"
                
                elif template['tipo'] == 'cita_confirmada':
                    if cita:
                        tecnico_nombre = cita.tecnico.usuario.get_full_name() or cita.tecnico.usuario.username
                        fecha_cita = cita.fecha_cita.strftime('%d/%m/%Y')
                        hora_cita = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
                        mensaje = f"""Estimado(a) {propietario.nombre},

Su cita para el reclamo {reclamo.folio} ha sido confirmada.

DETALLES DE LA CITA:
- Fecha: {fecha_cita}
- Hora: {hora_cita}
- Técnico: {tecnico_nombre}
- Reclamo: {reclamo.categoria.nombre}

Por favor, esté disponible en el horario acordado y asegúrese de que el técnico pueda acceder al área afectada.

Si necesita reprogramar, puede hacerlo desde la plataforma.

Saludos cordiales,
Equipo de Postventa"""
                    else:
                        mensaje = f"Estimado(a) {propietario.nombre},\n\nSu cita ha sido confirmada. El técnico visitará su propiedad según lo programado.\n\nSaludos cordiales,\nEquipo de Postventa"
                
                elif template['tipo'] == 'reclamo_resuelto':
                    mensaje = f"""Estimado(a) {propietario.nombre},

Nos complace informarle que su reclamo {reclamo.folio} ha sido marcado como resuelto.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Estado: Resuelto

Le agradeceremos que califique el servicio recibido ingresando a la plataforma. Su opinión es muy importante para nosotros y nos ayuda a mejorar continuamente.

Si el problema persiste o tiene alguna observación, por favor no dude en contactarnos.

Saludos cordiales,
Equipo de Postventa"""
                
                asunto = template['asunto'].format(folio=reclamo.folio)
                
                Notificacion.objects.create(
                    propietario=propietario,
                    reclamo=reclamo,
                    cita=cita,
                    asunto=asunto,
                    mensaje=mensaje,
                    estado=estado,
                    fecha_creacion=fecha_creacion,
                    fecha_envio=fecha_envio,
                    fecha_lectura=fecha_lectura,
                    intentos_envio=1 if estado != 'pendiente' else 0
                )
                contador += 1
                self.stdout.write(f'   ✓ Email: {asunto} → {propietario.nombre}')
        
        # Notificaciones para técnicos
        for i, template in enumerate([n for n in notificaciones_templates if n['destinatario'] == 'tecnico']):
            if tecnicos.exists() and reclamos.exists():
                tecnico = tecnicos[i % len(tecnicos)]
                reclamo = reclamos[i % len(reclamos)]
                cita = citas[i % len(citas)] if citas.exists() else None
                estado = estados[i % len(estados)]
                
                fecha_creacion = timezone.now() - timedelta(days=3-i)
                fecha_envio = None
                fecha_lectura = None
                
                if estado in ['enviada', 'leida']:
                    fecha_envio = fecha_creacion + timedelta(minutes=2)
                    
                if estado == 'leida':
                    fecha_lectura = fecha_envio + timedelta(hours=1)
                
                # Generar mensaje personalizado según tipo
                tecnico_nombre = tecnico.usuario.get_full_name() or tecnico.usuario.username
                
                if template['tipo'] == 'nuevo_reclamo':
                    propietario_nombre = reclamo.propietario.nombre if reclamo.propietario else 'No especificado'
                    mensaje = f"""Estimado(a) {tecnico_nombre},

Se le ha asignado un nuevo reclamo que requiere su atención.

DETALLES DEL RECLAMO:
- Folio: {reclamo.folio}
- Categoría: {reclamo.categoria.nombre}
- Propietario: {propietario_nombre}
- Proyecto: {reclamo.proyecto.nombre}
- Unidad: {reclamo.propietario.unidad if reclamo.propietario else 'N/A'}
- Ubicación: {reclamo.ubicacion_especifica}
- Descripción: {reclamo.descripcion[:150]}{'...' if len(reclamo.descripcion) > 150 else ''}

Por favor, revise los detalles completos en su panel y coordine la visita con el propietario a la brevedad. Puede comunicarse con el propietario al teléfono: {reclamo.propietario.telefono if reclamo.propietario else 'N/A'}

Saludos,
Equipo de Postventa"""
                
                elif template['tipo'] == 'recordatorio_visita':
                    if cita:
                        propietario_nombre = cita.reclamo.propietario.nombre if cita.reclamo.propietario else 'No especificado'
                        hora_cita = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
                        mensaje = f"""Estimado(a) {tecnico_nombre},

Este es un recordatorio de que tiene una visita programada para el día de hoy.

DETALLES DE LA CITA:
- Hora: {hora_cita}
- Reclamo: {cita.reclamo.folio}
- Categoría: {cita.reclamo.categoria.nombre}
- Propietario: {propietario_nombre}
- Ubicación: {cita.reclamo.ubicacion_especifica}
- Teléfono: {cita.reclamo.propietario.telefono if cita.reclamo.propietario else 'N/A'}

Por favor revise su agenda y confirme que cuenta con los materiales y herramientas necesarios para realizar el trabajo.

Saludos,
Equipo de Postventa"""
                    else:
                        mensaje = f"Estimado(a) {tecnico_nombre},\n\nRecuerde que tiene una visita programada para hoy. Revise su agenda.\n\nSaludos,\nEquipo de Postventa"
                
                elif template['tipo'] == 'cita_reprogramada':
                    if cita:
                        fecha_nueva = cita.fecha_cita.strftime('%d/%m/%Y')
                        hora_nueva = cita.hora_inicio.strftime('%H:%M') if cita.hora_inicio else 'Por confirmar'
                        mensaje = f"""Estimado(a) {tecnico_nombre},

Una de sus citas ha sido reprogramada.

NUEVA INFORMACIÓN:
- Reclamo: {reclamo.folio}
- Nueva fecha: {fecha_nueva}
- Nueva hora: {hora_nueva}
- Propietario: {reclamo.propietario.nombre if reclamo.propietario else 'N/A'}
- Ubicación: {reclamo.ubicacion_especifica}

Por favor verifique su calendario actualizado en la plataforma y coordine con el propietario si es necesario.

Saludos,
Equipo de Postventa"""
                    else:
                        mensaje = f"Estimado(a) {tecnico_nombre},\n\nUna cita ha sido reprogramada. Verifique su calendario.\n\nSaludos,\nEquipo de Postventa"
                
                asunto = template['asunto'].format(folio=reclamo.folio)
                
                Notificacion.objects.create(
                    tecnico=tecnico,
                    reclamo=reclamo,
                    cita=cita,
                    asunto=asunto,
                    mensaje=mensaje,
                    estado=estado,
                    fecha_creacion=fecha_creacion,
                    fecha_envio=fecha_envio,
                    fecha_lectura=fecha_lectura,
                    intentos_envio=1 if estado != 'pendiente' else 0
                )
                contador += 1
                self.stdout.write(f'   ✓ Email: {asunto} → {tecnico_nombre}')
        
        return contador
