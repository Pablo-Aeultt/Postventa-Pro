from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Unidad, Proyecto


class Command(BaseCommand):
    help = 'Asigna unidades a propietarios según el proyecto'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n📦 Iniciando asignación de unidades a propietarios...\n'))
        
        # Mapeo de asignaciones: (nombre_proyecto, rut_propietario, unidades_a_asignar)
        asignaciones = [
            # Edificio Apoquindo (6 unidades)
            ('Edificio Apoquindo', '98.765.432-1', ['Depto 101']),  # Ana Torres
            ('Edificio Apoquindo', '17.456.789-2', ['Depto 102']),  # Carlos Fuentes
            ('Edificio Apoquindo', '44.444.444-4', ['Depto 201', 'Depto 202']),  # Carmen Morales (2 unidades)
            ('Edificio Apoquindo', '14.567.890-9', ['Depto 301']),  # Daniela Paz
            ('Edificio Apoquindo', '21.234.567-1', ['Depto 302']),  # Felipe Torres
            
            # Condominio Parque Riesco (5 unidades)
            ('Condominio Parque Riesco', '77.123.456-4', ['Casa 1', 'Casa 2']),  # Inmobiliaria Renta Plus (2 unidades)
            ('Condominio Parque Riesco', '76.543.210-K', ['Casa 3']),  # Inmobiliaria XYZ
            ('Condominio Parque Riesco', '76.890.123-2', ['Casa 4', 'Casa 5']),  # Inversiones Providencia (2 unidades)
            
            # Torre SalfaCorp (5 unidades)
            ('Torre SalfaCorp', '20.123.456-7', ['Of. 501']),  # Jorge Morales
            ('Torre SalfaCorp', '11.111.111-1', ['Of. 502', 'Of. 503']),  # Juan Pérez (2 unidades)
            ('Torre SalfaCorp', '22.222.222-2', ['Of. 601', 'Of. 602']),  # María González (2 unidades)
        ]
        
        asignados = 0
        errores = 0
        
        for proyecto_nombre, rut, unidades_nombres in asignaciones:
            try:
                # Obtener proyecto por nombre completo
                proyecto = Proyecto.objects.get(nombre=proyecto_nombre)
                
                # Obtener propietario
                propietario = Propietario.objects.get(rut=rut)
                
                # Asignar cada unidad
                for unidad_nombre in unidades_nombres:
                    try:
                        unidad = Unidad.objects.get(nombre=unidad_nombre, proyecto=proyecto)
                        unidad.cliente = propietario
                        unidad.save()
                        asignados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {unidad_nombre} → {propietario.nombre}')
                        )
                    except Unidad.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Unidad no encontrada: {unidad_nombre} en {proyecto.nombre}')
                        )
                        errores += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error asignando {unidad_nombre}: {str(e)}')
                        )
                        errores += 1
                        
            except Proyecto.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Proyecto no encontrado: {proyecto_nombre}')
                )
                errores += 1
            except Propietario.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Propietario no encontrado con RUT: {rut}')
                )
                errores += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error en asignación: {str(e)}')
                )
                errores += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Asignación completada: {asignados} unidades asignadas')
        )
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(f'⚠️  {errores} errores encontrados\n')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sin errores\n')
            )
