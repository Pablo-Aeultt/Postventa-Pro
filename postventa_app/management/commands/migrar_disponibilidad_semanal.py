"""
Comando Django para migrar disponibilidades a patrón semanal repetitivo.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from django.core.management.base import BaseCommand
from postventa_app.models import Tecnico, Disponibilidad


class Command(BaseCommand):
    help = 'Migra disponibilidades por fecha a un patrón semanal repetitivo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('MIGRACIÓN A DISPONIBILIDAD SEMANAL'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Agrupar disponibilidades por técnico y día de la semana
        patrones = defaultdict(lambda: defaultdict(set))  # tecnico -> dia_semana -> {(hora_inicio, hora_fin)}
        
        disponibilidades = Disponibilidad.objects.all().order_by('id_tecnico', 'fecha')
        
        self.stdout.write(f'\nAnalizando {disponibilidades.count()} disponibilidades existentes...')
        
        for disp in disponibilidades:
            dia_semana = disp.fecha.weekday()  # 0=Lunes, 6=Domingo
            hora_clave = (str(disp.hora_inicio), str(disp.hora_fin))
            patrones[disp.id_tecnico][dia_semana].add(hora_clave)
        
        # Crear nuevas disponibilidades basadas en los patrones identificados
        hoy = datetime.now().date()
        nuevos_registros = 0
        
        for tecnico_id, dias in patrones.items():
            tecnico = tecnico_id if isinstance(tecnico_id, Tecnico) else Tecnico.objects.get(id_tecnico=tecnico_id)
            self.stdout.write(f'\n📋 Técnico: {tecnico.nombre}')
            
            for dia_semana, horarios in sorted(dias.items()):
                dia_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana]
                
                for hora_inicio_str, hora_fin_str in sorted(horarios):
                    self.stdout.write(f'   📅 {dia_nombre}: {hora_inicio_str[:5]} - {hora_fin_str[:5]}')
                    
                    # Calcular la próxima fecha de este día de la semana a partir de hoy
                    dias_adelante = (dia_semana - hoy.weekday()) % 7
                    
                    # Crear 12 semanas de disponibilidades futuras
                    for semana in range(12):
                        fecha = hoy + timedelta(days=dias_adelante + (semana * 7))
                        
                        # Evitar crear duplicados
                        existe = Disponibilidad.objects.filter(
                            id_tecnico=tecnico,
                            fecha=fecha,
                            hora_inicio=hora_inicio_str,
                            hora_fin=hora_fin_str
                        ).exists()
                        
                        if not existe:
                            Disponibilidad.objects.create(
                                id_tecnico=tecnico,
                                fecha=fecha,
                                hora_inicio=hora_inicio_str,
                                hora_fin=hora_fin_str
                            )
                            nuevos_registros += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ MIGRACIÓN COMPLETADA'))
        self.stdout.write(f'   - Nuevos registros creados: {nuevos_registros}')
        self.stdout.write('=' * 60)
        self.stdout.write('\n💡 IMPORTANTE:')
        self.stdout.write('   Los horarios ahora se repiten automáticamente cada semana.')
        self.stdout.write('   Para modificar los horarios, simplemente edita/elimina las disponibilidades.')
        self.stdout.write('=' * 60)
