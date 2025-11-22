from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from postventa_app.models import Cliente
import random


class Command(BaseCommand):
    help = 'Elimina todos los clientes propietarios y crea los propietarios proporcionados.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Eliminando todos los clientes propietarios existentes...'))
        deleted, _ = Cliente.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Eliminados {deleted} registros.'))

        propietarios = [
            ("Ana Torres", "98.765.432-1", "ana.torres@gmail.com"),
            ("Carlos Fuentes Lagos", "17.456.789-2", "cfuentes@outlook.com"),
            ("Carmen Morales", "44.444.444-4", "carmen.morales@email.com"),
            ("Daniela Paz Soto Ramírez", "14.567.890-9", "dpsoto@icloud.com"),
            ("Felipe Ignacio Torres Muñoz", "21.234.567-1", "ftorres@gmail.com"),
            ("Inmobiliaria Renta Plus S.A.", "77.123.456-4", "contacto@rentaplus.cl"),
            ("Inmobiliaria XYZ S.A.", "76.543.210-K", "contacto@inmobiliariaxyz.cl"),
            ("Inversiones Providencia Limitada", "76.890.123-2", "contacto@invprovidencia.cl"),
            ("Jorge Andrés Morales Díaz", "20.123.456-7", "jmorales@gmail.com"),
            ("Juan Pérez", "11.111.111-1", "juan.perez@email.com"),
            ("María González", "22.222.222-2", "maria.gonzalez@email.com"),
            ("María José Contreras Vera", "19.012.345-3", "mjcontreras@yahoo.com"),
            ("Patricia González Silva", "18.234.890-5", "pgonzalez@hotmail.com"),
            ("Roberto Silva", "33.333.333-3", "roberto.silva@email.com"),
            ("Rodrigo Valdivia Parra", "16.789.012-K", "rvaldivia@gmail.com"),
            ("Valentina Alejandra Vásquez Bravo", "13.890.123-6", "vvasquez@outlook.com"),
        ]

        for nombre, rut, email in propietarios:
            username = rut.replace('.', '').replace('-', '').replace('K', 'k')
            self.stdout.write(f"Procesando: {nombre} (RUT: {rut})")
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombre.split()[0],
                    'last_name': ' '.join(nombre.split()[1:]),
                    'email': email,
                }
            )
            if created:
                user.set_password('propietario123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username} | Email: {email}"))
            else:
                self.stdout.write(self.style.WARNING(f"Usuario ya existe: {username}"))

            cliente = Cliente.objects.filter(rut=rut).first()
            if not cliente:
                self.stdout.write(f"  -> Creando cliente...")
                cliente = Cliente.objects.create(
                    rut=rut,
                    nombre=nombre,
                    email=email,
                    user=user,
                    telefono=f'+56 9 {random.randint(10000000,99999999)}',
                    direccion='',
                    unidad='',
                    observaciones='',
                    comuna='',
                    region='',
                    estado='activo',
                )
                self.stdout.write(self.style.SUCCESS(f"Cliente creado: {cliente.nombre} (ID: {cliente.id_cliente}) -> {user.username}"))
            else:
                self.stdout.write(f"  -> Actualizando cliente...")
                cliente.user = user
                cliente.nombre = nombre
                cliente.email = email
                cliente.estado = 'activo'
                cliente.save()
                self.stdout.write(self.style.SUCCESS(f"Cliente vinculado/actualizado: {cliente.nombre} -> {user.username}"))

        total = Cliente.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Carga de propietarios completada. Total clientes: {total}'))
