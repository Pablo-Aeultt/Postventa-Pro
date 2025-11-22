from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from postventa_app.models import Cliente, Proyecto, Unidad
import random


class Command(BaseCommand):
    help = 'Crea unidades en los proyectos y asigna clientes propietarios a proyectos/unidades.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creando unidades en proyectos...'))
        
        # Crear unidades por proyecto
        proyectos_unidades = {
            1: ['Depto 101', 'Depto 102', 'Depto 201', 'Depto 202', 'Depto 301', 'Depto 302'],
            2: ['Casa 1', 'Casa 2', 'Casa 3', 'Casa 4', 'Casa 5'],
            3: ['Of. 501', 'Of. 502', 'Of. 503', 'Of. 601', 'Of. 602'],
        }
        
        for proyecto_id, nombres_unidades in proyectos_unidades.items():
            proyecto = Proyecto.objects.get(id_proyecto=proyecto_id)
            for nombre in nombres_unidades:
                unidad, created = Unidad.objects.get_or_create(
                    nombre=nombre,
                    proyecto=proyecto,
                    defaults={'cliente': None}
                )
                if created:
                    self.stdout.write(f"  ✓ Unidad creada: {nombre} en {proyecto.nombre}")
        
        self.stdout.write(self.style.SUCCESS(f'Total de unidades creadas: {Unidad.objects.count()}'))
        
        # Asignar clientes a proyectos y unidades
        self.stdout.write(self.style.WARNING('\nAsignando clientes a proyectos y unidades...'))
        
        clientes = Cliente.objects.all().order_by('id_cliente')
        proyectos = Proyecto.objects.all()
        
        # Distribución: algunos clientes con una unidad, otros con múltiples
        distribucion = [
            (1, 1),  # Cliente 1: 1 proyecto, 1 unidad
            (1, 1),  # Cliente 2: 1 proyecto, 1 unidad
            (1, 2),  # Cliente 3: 1 proyecto, 2 unidades
            (1, 1),  # Cliente 4: 1 proyecto, 1 unidad
            (1, 2),  # Cliente 5: 1 proyecto, 2 unidades
            (1, 1),  # Cliente 6: 1 proyecto, 1 unidad
            (1, 1),  # Cliente 7: 1 proyecto, 1 unidad
            (1, 3),  # Cliente 8: 1 proyecto, 3 unidades
            (1, 1),  # Cliente 9: 1 proyecto, 1 unidad
            (1, 2),  # Cliente 10: 1 proyecto, 2 unidades
            (1, 1),  # Cliente 11: 1 proyecto, 1 unidad
            (1, 1),  # Cliente 12: 1 proyecto, 1 unidad
            (1, 2),  # Cliente 13: 1 proyecto, 2 unidades
            (1, 1),  # Cliente 14: 1 proyecto, 1 unidad
            (1, 1),  # Cliente 15: 1 proyecto, 1 unidad
            (1, 2),  # Cliente 16: 1 proyecto, 2 unidades
        ]
        
        indice_unidad_global = 0
        todas_unidades = list(Unidad.objects.all().order_by('proyecto__id_proyecto', 'nombre'))
        
        for idx, cliente in enumerate(clientes):
            if idx < len(distribucion):
                num_proyectos, num_unidades = distribucion[idx]
                
                # Asignar la primera unidad como unidad principal del cliente
                if indice_unidad_global < len(todas_unidades):
                    unidad_principal = todas_unidades[indice_unidad_global]
                    cliente.unidad = unidad_principal.nombre
                    cliente.save()
                    unidad_principal.cliente = cliente
                    unidad_principal.save()
                    self.stdout.write(f"  ✓ {cliente.nombre}: {unidad_principal.nombre} ({unidad_principal.proyecto.nombre})")
                    indice_unidad_global += 1
                    
                    # Asignar unidades adicionales (no mostrar en cliente.unidad pero asociarlas)
                    for i in range(1, num_unidades):
                        if indice_unidad_global < len(todas_unidades):
                            unidad_adicional = todas_unidades[indice_unidad_global]
                            unidad_adicional.cliente = cliente
                            unidad_adicional.save()
                            self.stdout.write(f"       + {unidad_adicional.nombre} ({unidad_adicional.proyecto.nombre})")
                            indice_unidad_global += 1
        
        self.stdout.write(self.style.SUCCESS('Asignación de clientes completada.'))
        self.stdout.write(self.style.SUCCESS(f'Total de unidades asignadas: {Unidad.objects.filter(cliente__isnull=False).count()}'))
