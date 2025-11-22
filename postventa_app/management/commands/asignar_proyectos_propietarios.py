from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Proyecto


class Command(BaseCommand):
    help = 'Asigna proyectos a propietarios que no tienen'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🏢 Iniciando asignación de proyectos a propietarios...\n'))
        
        # Propietarios sin proyecto y sus asignaciones
        asignaciones = [
            ('19.012.345-3', 'Edificio Apoquindo'),  # María José Contreras
            ('18.234.890-5', 'Condominio Parque Riesco'),  # Patricia González
            ('33.333.333-3', 'Torre SalfaCorp'),  # Roberto Silva
            ('16.789.012-K', 'Edificio Apoquindo'),  # Rodrigo Valdivia
            ('13.890.123-6', 'Condominio Parque Riesco'),  # Valentina Vásquez
        ]
        
        asignados = 0
        errores = 0
        
        for rut, proyecto_nombre in asignaciones:
            try:
                propietario = Propietario.objects.get(rut=rut)
                proyecto = Proyecto.objects.get(nombre=proyecto_nombre)
                
                propietario.proyecto = proyecto
                propietario.save()
                asignados += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {propietario.nombre} → {proyecto.nombre}')
                )
            except Propietario.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Propietario no encontrado con RUT: {rut}')
                )
                errores += 1
            except Proyecto.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Proyecto no encontrado: {proyecto_nombre}')
                )
                errores += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error: {str(e)}')
                )
                errores += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Asignación completada: {asignados} propietarios asignados a proyectos')
        )
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(f'⚠️  {errores} errores encontrados\n')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sin errores\n')
            )
