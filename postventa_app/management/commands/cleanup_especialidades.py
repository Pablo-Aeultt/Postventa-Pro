from django.core.management.base import BaseCommand
from django.db import transaction
from postventa_app.models import Especialidad, Reclamo


class Command(BaseCommand):
    help = "Limpia especialidades con nombre vacío y desvincula reclamos asociados para evitar categorías sin nombre en KPIs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios que se realizarían sin aplicarlos",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        vacias = Especialidad.objects.filter(nombre__isnull=True) | Especialidad.objects.filter(nombre="") | Especialidad.objects.filter(nombre__regex=r"^\s+$")
        vacias = vacias.distinct()

        total_especialidades_vacias = vacias.count()
        reclamos_afectados = Reclamo.objects.filter(categoria__in=vacias)
        total_reclamos_afectados = reclamos_afectados.count()

        self.stdout.write(self.style.WARNING(f"Especialidades vacías: {total_especialidades_vacias}"))
        self.stdout.write(self.style.WARNING(f"Reclamos vinculados a especialidades vacías: {total_reclamos_afectados}"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry-run: no se aplican cambios"))
            return

        # Desvincular reclamos de especialidades vacías (set categoria = None)
        updated = reclamos_afectados.update(categoria=None)
        self.stdout.write(self.style.SUCCESS(f"Reclamos desvinculados: {updated}"))

        # Eliminar especialidades vacías
        deleted_info = vacias.delete()
        self.stdout.write(self.style.SUCCESS(f"Especialidades eliminadas: {deleted_info}"))

        self.stdout.write(self.style.SUCCESS("Limpieza completada."))
