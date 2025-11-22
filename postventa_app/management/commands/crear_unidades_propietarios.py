from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Unidad, Proyecto


class Command(BaseCommand):
    help = 'Crea y asigna nuevas unidades a propietarios que no tienen'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🏠 Creando nuevas unidades para propietarios...\n'))
        
        # Mapeo: (rut_propietario, proyecto_nombre, unidades_a_crear)
        asignaciones = [
            # María José Contreras - Edificio Apoquindo
            ('19.012.345-3', 'Edificio Apoquindo', ['Depto 401']),
            
            # Patricia González - Condominio Parque Riesco
            ('18.234.890-5', 'Condominio Parque Riesco', ['Casa 6']),
            
            # Roberto Silva - Torre SalfaCorp
            ('33.333.333-3', 'Torre SalfaCorp', ['Of. 701']),
            
            # Rodrigo Valdivia - Edificio Apoquindo
            ('16.789.012-K', 'Edificio Apoquindo', ['Depto 402']),
            
            # Valentina Vásquez - Condominio Parque Riesco
            ('13.890.123-6', 'Condominio Parque Riesco', ['Casa 7']),
        ]
        
        creadas = 0
        errores = 0
        
        for rut, proyecto_nombre, unidades_nombres in asignaciones:
            try:
                propietario = Propietario.objects.get(rut=rut)
                proyecto = Proyecto.objects.get(nombre=proyecto_nombre)
                
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
                            self.style.SUCCESS(f'✓ {unidad_nombre} creada para {propietario.nombre}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error creando {unidad_nombre}: {str(e)}')
                        )
                        errores += 1
                        
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
                    self.style.ERROR(f'✗ Error general: {str(e)}')
                )
                errores += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Proceso completado: {creadas} unidades creadas')
        )
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(f'⚠️  {errores} errores encontrados\n')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sin errores\n')
            )
