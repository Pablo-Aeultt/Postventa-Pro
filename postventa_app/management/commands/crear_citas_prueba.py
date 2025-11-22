"""
Script para crear citas de prueba para reclamos existentes con técnicos asignados
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from postventa_app.models import Reclamo, Cita, AsignacionTecnico
import random

class Command(BaseCommand):
    help = 'Crea citas de prueba para reclamos con técnicos asignados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de citas de prueba...'))
        
        # Obtener reclamos con asignaciones activas que no tengan citas
        asignaciones = AsignacionTecnico.objects.filter(estado='activa').select_related('id_reclamo', 'id_tecnico')
        
        citas_creadas = 0
        hoy = datetime.now()
        
        for asignacion in asignaciones:
            reclamo = asignacion.id_reclamo
            tecnico = asignacion.id_tecnico
            
            # Verificar si ya tiene una cita activa
            cita_existente = Cita.objects.filter(
                id_reclamo=reclamo,
                estado__in=['pendiente', 'confirmada']
            ).first()
            
            if not cita_existente:
                # Generar fecha aleatoria entre hoy y los próximos 14 días (solo lunes a viernes)
                fecha_cita = None
                intentos = 0
                while fecha_cita is None and intentos < 20:
                    dias_adelante = random.randint(1, 14)
                    fecha_temp = hoy + timedelta(days=dias_adelante)
                    # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado, 6=Domingo
                    if fecha_temp.weekday() < 5:  # Solo lunes a viernes
                        fecha_cita = fecha_temp
                    intentos += 1
                
                if fecha_cita is None:
                    continue
                
                # Horarios posibles: 09:00, 10:00, 11:00, 12:00 (mañana) y 14:00, 15:00, 16:00, 17:00 (tarde)
                horas_posibles = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00']
                hora_seleccionada = random.choice(horas_posibles)
                
                # Combinar fecha y hora
                hora, minuto = map(int, hora_seleccionada.split(':'))
                fecha_programada = fecha_cita.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                
                # Crear la cita
                Cita.objects.create(
                    id_reclamo=reclamo,
                    id_tecnico=tecnico,
                    id_cliente=reclamo.id_cliente,
                    fecha_programada=fecha_programada,
                    estado='pendiente',
                    tipo_cita='visita_tecnica',
                    duracion_estimada_minutos=120
                )
                
                citas_creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Cita creada para Reclamo {reclamo.numero_folio} - '
                        f'Técnico: {tecnico.nombre} - '
                        f'Fecha: {fecha_programada.strftime("%d/%m/%Y %H:%M")}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'Proceso completado!\n'
                f'Total de citas creadas: {citas_creadas}\n'
                f'{"="*60}'
            )
        )
