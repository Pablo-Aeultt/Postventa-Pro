"""
Comando para marcar las disponibilidades existentes como recurrentes
y asignarles el día de semana correcto.
"""

from django.core.management.base import BaseCommand
from postventa_app.models import Disponibilidad


class Command(BaseCommand):
    help = 'Marca las disponibilidades existentes como recurrentes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('MARCANDO DISPONIBILIDADES COMO RECURRENTES'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Obtener todas las disponibilidades
        disponibilidades = Disponibilidad.objects.all()
        actualizadas = 0
        
        for disp in disponibilidades:
            # Obtener el día de semana de la fecha
            dia_semana = disp.fecha.weekday()  # 0=Lunes, 6=Domingo
            
            # Actualizar
            disp.es_recurrente = True
            disp.dia_semana = dia_semana
            disp.save()
            actualizadas += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✅ ACTUALIZACIÓN COMPLETADA'))
        self.stdout.write(f'   - Disponibilidades actualizadas: {actualizadas}')
        self.stdout.write('=' * 60)
        self.stdout.write('\n💡 AHORA:')
        self.stdout.write('   Los horarios son RECURRENTES (se repiten cada semana)')
        self.stdout.write('   Puedes eliminar los registros duplicados si lo deseas.')
        self.stdout.write('=' * 60)
