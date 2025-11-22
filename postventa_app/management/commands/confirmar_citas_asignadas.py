from django.core.management.base import BaseCommand
from django.utils import timezone

from postventa_app.models import Cita, Reclamo


class Command(BaseCommand):
    help = (
        "Marca como confirmadas las citas pendientes cuyos reclamos están asignados o en proceso. "
        "Setea fecha_confirmacion si está vacía. Muestra un resumen del cambio."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No guarda cambios, solo muestra cuántos registros serían afectados.",
        )

    def handle(self, *args, **options):
        qs = Cita.objects.filter(
            estado="pendiente",
            reclamo__estado__in=["asignado", "en_proceso"],
        )
        total = qs.count()
        if options.get("dry_run"):
            self.stdout.write(self.style.WARNING(f"[DRY-RUN] Citas a confirmar: {total}"))
            return

        ahora = timezone.now()
        actualizados = 0
        for c in qs.iterator():
            c.estado = "confirmada"
            if not c.fecha_confirmacion:
                c.fecha_confirmacion = ahora
            c.save(update_fields=["estado", "fecha_confirmacion"])
            actualizados += 1

        self.stdout.write(self.style.SUCCESS(f"Citas confirmadas: {actualizados} (de {total})"))
