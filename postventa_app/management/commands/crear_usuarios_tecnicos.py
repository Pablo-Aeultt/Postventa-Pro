from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from postventa_app.models import Tecnico

class Command(BaseCommand):
    help = "Crea usuarios Django para todos los técnicos que no tengan usuario y les asigna la contraseña 'tecnico123'. El username será el rut (sin puntos ni guion) o el email si no hay rut."

    def handle(self, *args, **options):
        password = "tecnico123"
        creados = 0
        actualizados = 0
        for tecnico in Tecnico.objects.all():
            # Username preferente: rut sin puntos ni guion, si no hay rut usa email
            username = None
            if tecnico.rut:
                username = tecnico.rut.replace(".", "").replace("-", "")
            elif tecnico.email:
                username = tecnico.email
            else:
                self.stdout.write(self.style.WARNING(f"Técnico sin rut ni email: {tecnico.nombre}"))
                continue

            # Buscar usuario por username o email
            user = User.objects.filter(username=username).first()
            if not user and tecnico.email:
                user = User.objects.filter(email=tecnico.email).first()

            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=tecnico.email or '',
                    password=password,
                    first_name=tecnico.nombre or '',
                )
                creados += 1
                self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username}"))
            else:
                user.set_password(password)
                user.email = tecnico.email or user.email
                user.first_name = tecnico.nombre or user.first_name
                user.save()
                actualizados += 1
                self.stdout.write(self.style.NOTICE(f"Usuario actualizado: {username}"))

            # Vincular usuario al técnico si hay campo usuario
            if hasattr(tecnico, 'usuario_id'):
                tecnico.usuario = user
                tecnico.save(update_fields=['usuario'])

        self.stdout.write(self.style.SUCCESS(f"Usuarios creados: {creados}, actualizados: {actualizados}"))
        self.stdout.write(self.style.HTTP_INFO("Contraseña para todos: tecnico123"))
