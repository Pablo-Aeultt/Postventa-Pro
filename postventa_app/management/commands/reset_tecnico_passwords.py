from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from postventa_app.models import Tecnico


class Command(BaseCommand):
    help = (
        "Resetea la contraseña de todas las cuentas de usuario vinculadas a Tecnico. "
        "Uso: manage.py reset_tecnico_passwords --password NUEVA_CLAVE"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            dest="password",
            type=str,
            default="Tecnico123!",
            help="Contraseña a establecer para TODOS los técnicos (default: Tecnico123!)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué usuarios serían actualizados sin aplicar cambios",
        )

    def handle(self, *args, **options):
        password = options["password"]
        dry_run = options["dry_run"]

        tecnicos = Tecnico.objects.select_related("usuario").all()
        total = tecnicos.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No hay técnicos registrados."))
            return

        updated = 0
        usernames = []
        for t in tecnicos:
            user = t.usuario
            if not isinstance(user, User):
                continue
            usernames.append(user.username)
            if not dry_run:
                user.set_password(password)
                user.save(update_fields=["password"])
                updated += 1

        if dry_run:
            self.stdout.write(self.style.NOTICE("DRY RUN: No se aplicaron cambios"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Técnicos encontrados: {total} | Cuentas actualizadas: {updated if not dry_run else 0}"
            )
        )
        self.stdout.write("Usuarios afectados:")
        for u in usernames:
            self.stdout.write(f" - {u}")

        if not dry_run:
            self.stdout.write(self.style.HTTP_INFO("Recuerda iniciar sesión con la nueva contraseña especificada."))
