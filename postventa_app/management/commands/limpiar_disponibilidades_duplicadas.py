"""
Comando para limpiar disponibilidades duplicadas.
Mantiene solo UN registro por (técnico, día_semana, hora_inicio, hora_fin).
"""

from django.core.management.base import BaseCommand
from postventa_app.models import Disponibilidad
from django.db.models import Min


class Command(BaseCommand):
    help = 'Elimina disponibilidades duplicadas, mantiene solo una por semana'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('LIMPIANDO DISPONIBILIDADES DUPLICADAS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Obtener todas las disponibilidades agrupadas por técnico, día_semana y horario
        disponibilidades = Disponibilidad.objects.filter(es_recurrente=True)
        
        grupos = {}
        eliminadas = 0
        
        for disp in disponibilidades:
            clave = (disp.id_tecnico_id, disp.dia_semana, str(disp.hora_inicio), str(disp.hora_fin))
            
            if clave not in grupos:
                grupos[clave] = []
            grupos[clave].append(disp)
        
        # Para cada grupo, mantener solo el primero y eliminar los demás
        for clave, grupo in grupos.items():
            if len(grupo) > 1:
                self.stdout.write(f'  Grupo: Técnico {grupo[0].id_tecnico.nombre}, '
                                f'{grupo[0].get_dia_semana_display_custom()}, '
                                f'{grupo[0].hora_inicio}-{grupo[0].hora_fin}')
                self.stdout.write(f'    - Encontrados: {len(grupo)}, eliminando {len(grupo)-1}')
                
                # Mantener el primero (el más antiguo por created_at)
                a_mantener = sorted(grupo, key=lambda x: x.created_at)[0]
                
                for disp in grupo:
                    if disp.id_disponibilidad != a_mantener.id_disponibilidad:
                        disp.delete()
                        eliminadas += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✅ LIMPIEZA COMPLETADA'))
        self.stdout.write(f'   - Registros eliminados: {eliminadas}')
        self.stdout.write('=' * 60)
        self.stdout.write('\n💡 RESULTADO:')
        self.stdout.write('   ✓ Base de datos limpia')
        self.stdout.write('   ✓ Horarios recurrentes (se repiten cada semana)')
        self.stdout.write('   ✓ Ocupan mínimo espacio')
        self.stdout.write('=' * 60)
