from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from postventa_app.models import Propietario, Proyecto


class Command(BaseCommand):
    help = 'Crea un propietario con su usuario del sistema'

    def add_arguments(self, parser):
        parser.add_argument('--rut', type=str, required=True, help='RUT del propietario')
        parser.add_argument('--nombre', type=str, required=True, help='Nombre completo')
        parser.add_argument('--email', type=str, required=True, help='Email')
        parser.add_argument('--telefono', type=str, required=True, help='Teléfono')
        parser.add_argument('--direccion', type=str, required=True, help='Dirección')
        parser.add_argument('--proyecto-id', type=int, required=False, help='ID del proyecto (opcional)')
        parser.add_argument('--unidad', type=str, required=False, help='Número de unidad (opcional)')

    def handle(self, *args, **options):
        rut = options['rut']
        nombre = options['nombre']
        email = options['email']
        telefono = options['telefono']
        direccion = options['direccion']
        proyecto_id = options.get('proyecto_id')
        unidad = options.get('unidad')

        # Generar username desde RUT (sin puntos ni guión)
        username = rut.replace('.', '').replace('-', '')
        password = username  # Password inicial = RUT sin formato

        try:
            # Verificar si ya existe
            if Propietario.objects.filter(rut=rut).exists():
                self.stdout.write(self.style.ERROR(f'❌ Ya existe un propietario con RUT {rut}'))
                return

            # Crear usuario
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                self.stdout.write(self.style.WARNING(f'⚠️  Usuario {username} ya existe, se reutilizará'))
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario creado: {username}'))

            # Obtener proyecto si se especificó
            proyecto = None
            if proyecto_id:
                try:
                    proyecto = Proyecto.objects.get(id=proyecto_id)
                except Proyecto.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️  Proyecto con ID {proyecto_id} no existe'))

            # Crear propietario
            propietario = Propietario.objects.create(
                user=user,
                rut=rut,
                nombre=nombre,
                email=email,
                telefono=telefono,
                direccion=direccion,
                proyecto=proyecto,
                unidad=unidad,
                estado='activo'
            )

            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✓ PROPIETARIO CREADO EXITOSAMENTE'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(f'Nombre: {nombre}')
            self.stdout.write(f'RUT: {rut}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Teléfono: {telefono}')
            if proyecto:
                self.stdout.write(f'Proyecto: {proyecto.nombre}')
            if unidad:
                self.stdout.write(f'Unidad: {unidad}')
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CREDENCIALES DE ACCESO:'))
            self.stdout.write(self.style.WARNING(f'Usuario: {username}'))
            self.stdout.write(self.style.WARNING(f'Contraseña: {password}'))
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.SUCCESS(f'URL: http://127.0.0.1:8000/login/'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
