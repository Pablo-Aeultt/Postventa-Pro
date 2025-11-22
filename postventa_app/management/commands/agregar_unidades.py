from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Unidad, Proyecto


class Command(BaseCommand):
    help = 'Agrega unidades adicionales a un propietario'

    def add_arguments(self, parser):
        parser.add_argument('rut', type=str, help='RUT del propietario')
        parser.add_argument('--proyecto', type=str, help='Nombre del proyecto')
        parser.add_argument('--unidades', type=str, nargs='+', help='Nombres de las unidades a crear')

    def handle(self, *args, **options):
        rut = options['rut']
        proyecto_nombre = options.get('proyecto')
        unidades_nombres = options.get('unidades', [])
        
        try:
            propietario = Propietario.objects.get(rut=rut)
            self.stdout.write(self.style.SUCCESS(f'\n✓ Propietario encontrado: {propietario.nombre}\n'))
            
            if not proyecto_nombre:
                proyecto_nombre = propietario.proyecto.nombre if propietario.proyecto else None
                
            if not proyecto_nombre:
                self.stdout.write(self.style.ERROR('✗ Debes especificar un proyecto'))
                return
                
            proyecto = Proyecto.objects.get(nombre=proyecto_nombre)
            self.stdout.write(self.style.SUCCESS(f'✓ Proyecto: {proyecto.nombre}\n'))
            
            creadas = 0
            for unidad_nombre in unidades_nombres:
                try:
                    # Verificar que no exista ya
                    if Unidad.objects.filter(nombre=unidad_nombre, proyecto=proyecto).exists():
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  {unidad_nombre} ya existe en {proyecto.nombre}')
                        )
                        continue
                    
                    # Crear la unidad
                    unidad = Unidad.objects.create(
                        nombre=unidad_nombre,
                        proyecto=proyecto,
                        cliente=propietario,
                        descripcion=f'Unidad de {propietario.nombre}'
                    )
                    creadas += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {unidad_nombre} agregada a {propietario.nombre}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error creando {unidad_nombre}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ {creadas} unidades agregadas\n')
            )
            
        except Propietario.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ Propietario no encontrado con RUT: {rut}')
            )
        except Proyecto.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ Proyecto no encontrado: {proyecto_nombre}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            )
