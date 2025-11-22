"""
Script para asignar horarios de disponibilidad a los técnicos
"""
from django.core.management.base import BaseCommand
from postventa_app.models import Tecnico
import json

class Command(BaseCommand):
    help = 'Asigna horarios de disponibilidad a los técnicos (Lunes a Viernes, 9:00-18:00)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando asignación de horarios a técnicos...'))
        
        # Definir horarios estándar: Lunes a Viernes, 9:00-13:00 y 14:00-18:00
        horarios_estandar = {
            "dias_laborales": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            "horarios": [
                {
                    "bloque": "mañana",
                    "hora_inicio": "09:00",
                    "hora_fin": "13:00",
                    "disponible": True
                },
                {
                    "bloque": "tarde",
                    "hora_inicio": "14:00",
                    "hora_fin": "18:00",
                    "disponible": True
                }
            ],
            "dias_semana": {
                "Lunes": {
                    "activo": True,
                    "horarios": [
                        {"hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"hora_inicio": "14:00", "hora_fin": "18:00"}
                    ]
                },
                "Martes": {
                    "activo": True,
                    "horarios": [
                        {"hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"hora_inicio": "14:00", "hora_fin": "18:00"}
                    ]
                },
                "Miércoles": {
                    "activo": True,
                    "horarios": [
                        {"hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"hora_inicio": "14:00", "hora_fin": "18:00"}
                    ]
                },
                "Jueves": {
                    "activo": True,
                    "horarios": [
                        {"hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"hora_inicio": "14:00", "hora_fin": "18:00"}
                    ]
                },
                "Viernes": {
                    "activo": True,
                    "horarios": [
                        {"hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"hora_inicio": "14:00", "hora_fin": "18:00"}
                    ]
                },
                "Sábado": {
                    "activo": False,
                    "horarios": []
                },
                "Domingo": {
                    "activo": False,
                    "horarios": []
                }
            }
        }
        
        # Obtener todos los técnicos activos
        tecnicos = Tecnico.objects.filter(estado='activo')
        
        tecnicos_actualizados = 0
        
        for tecnico in tecnicos:
            # Asignar horarios estándar
            tecnico.disponibilidad_horaria = horarios_estandar
            tecnico.save()
            
            tecnicos_actualizados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Horarios asignados a: {tecnico.nombre} ({tecnico.especialidad})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'Proceso completado!\n'
                f'Total de técnicos actualizados: {tecnicos_actualizados}\n'
                f'Horarios: Lunes a Viernes, 9:00-13:00 y 14:00-18:00\n'
                f'{"="*60}'
            )
        )
