from django.core.management.base import BaseCommand
from postventa_app.models import Propietario
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Asigna usuario a un propietario por RUT. Uso: --rut <RUT>'

    def add_arguments(self, parser):
        parser.add_argument('--rut', type=str, required=True, help='RUT del propietario')

    def handle(self, *args, **options):
        rut = options['rut']
        propietario = Propietario.objects.filter(rut__iexact=rut).first()
        if not propietario:
            self.stdout.write(self.style.ERROR(f'No se encontró propietario con RUT {rut}'))
            return
        rut_limpio = rut.replace('.', '').replace('-', '')
        user = User.objects.filter(username=rut_limpio).first()
        if propietario.user:
            self.stdout.write(self.style.SUCCESS(f'El propietario {propietario.nombre} ya tiene usuario vinculado.'))
            return
        if not user:
            user = User.objects.create_user(
                username=rut_limpio,
                email=propietario.email or '',
                password='propietario123',
                first_name=propietario.nombre.split()[0] if propietario.nombre else '',
                last_name=' '.join(propietario.nombre.split()[1:]) if propietario.nombre else ''
            )
            self.stdout.write(self.style.SUCCESS(f'Usuario creado para {propietario.nombre} (RUT: {rut})'))
        else:
            self.stdout.write(self.style.WARNING(f'Usuario ya existía para {propietario.nombre} (RUT: {rut})'))
        propietario.user = user
        propietario.save()
        self.stdout.write(self.style.SUCCESS(f'Usuario vinculado correctamente a {propietario.nombre}'))
