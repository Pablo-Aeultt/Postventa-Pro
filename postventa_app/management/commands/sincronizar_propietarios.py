from django.core.management.base import BaseCommand
from postventa_app.models import Cliente, Propietario, Unidad, Proyecto
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Sincroniza clientes propietarios a la tabla Propietario con unidades y proyectos.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Limpiando propietarios existentes...'))
        Propietario.objects.all().delete()

        self.stdout.write(self.style.WARNING('Creando propietarios desde clientes...'))
        
        clientes = Cliente.objects.all().order_by('id_cliente')
        propietarios_creados = 0
        
        for cliente in clientes:
            # Obtener la unidad del cliente si existe
            unidad_obj = None
            proyecto_obj = None
            
            if cliente.unidad:
                # Buscar la unidad por nombre
                unidad_obj = Unidad.objects.filter(nombre=cliente.unidad, cliente=cliente).first()
                if unidad_obj:
                    proyecto_obj = unidad_obj.proyecto
            
            # Determinar tipo de propietario (simplista: si contiene "S.A." o "Limitada" es jurídica)
            tipo = 'juridica' if any(x in cliente.nombre for x in ['S.A.', 'Limitada', 'LTDA', 'Inmobiliaria']) else 'natural'
            
            propietario = Propietario.objects.create(
                user=cliente.user,
                nombre=cliente.nombre,
                rut=cliente.rut,
                tipo_propietario=tipo,
                email=cliente.email,
                telefono=cliente.telefono or f'+56 9 {random.randint(10000000,99999999)}',
                telefono_alternativo='',
                direccion=cliente.direccion or '',
                proyecto=proyecto_obj,
                unidad=cliente.unidad or '',
                fecha_compra=date.today() - timedelta(days=random.randint(30, 365)),
                estado='activo',
                notas_internas=cliente.observaciones or '',
            )
            propietarios_creados += 1
            self.stdout.write(self.style.SUCCESS(f"✓ Propietario creado: {propietario.nombre} - Proyecto: {proyecto_obj.nombre if proyecto_obj else 'N/A'} - Unidad: {propietario.unidad}"))
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal de propietarios creados: {propietarios_creados}'))
        self.stdout.write(self.style.SUCCESS(f'Total de propietarios en BD: {Propietario.objects.count()}'))
