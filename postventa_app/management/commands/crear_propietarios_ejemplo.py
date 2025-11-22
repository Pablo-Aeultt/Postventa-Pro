from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Proyecto
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crea un ejemplo de propietario con dos viviendas en el mismo proyecto.'

    def handle(self, *args, **options):
        nombre = 'Marcela Fuentes'
        rut = '15.123.456-7'
        email = 'marcela.fuentes@gmail.com'
        telefono = '+56987654321'
        proyecto = Proyecto.objects.filter(nombre__icontains='Condominio Las Palmas').first()
        unidades = ['Depto 301', 'Depto 302']
        rut_limpio = rut.replace('.', '').replace('-', '')
        if not User.objects.filter(username=rut_limpio).exists():
            user = User.objects.create_user(
                username=rut_limpio,
                email=email,
                password='propietario123',
                first_name=nombre.split()[0],
                last_name=' '.join(nombre.split()[1:])
            )
        else:
            user = User.objects.get(username=rut_limpio)
        for unidad in unidades:
            propietario, created = Propietario.objects.get_or_create(
                unidad=unidad,
                proyecto=proyecto,
                defaults={
                    'rut': rut,
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'direccion': unidad,
                    'user': user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Propietario con dos viviendas creado: {nombre} ({rut}) - {unidad}"))
            else:
                self.stdout.write(f"Propietario con dos viviendas ya existía: {nombre} ({rut}) - {unidad}")
