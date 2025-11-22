from django.core.management.base import BaseCommand
from django.db import transaction
from postventa_app.models import Tecnico


def calc_dv(num: int) -> str:
    """Calcula dígito verificador del RUT chileno."""
    factors = [2, 3, 4, 5, 6, 7]
    s = 0
    i = 0
    while num > 0:
        s += (num % 10) * factors[i % len(factors)]
        num //= 10
        i += 1
    dv = 11 - (s % 11)
    if dv == 11:
        return '0'
    if dv == 10:
        return 'K'
    return str(dv)


def format_rut_number(n: int, dv: str) -> str:
    s = f"{n:,}".replace(',', '.')  # puntos cada 3
    return f"{s}-{dv}"


class Command(BaseCommand):
    help = (
        "Genera y asigna RUTs únicos a todos los técnicos que no tengan uno. "
        "Usa un rango base y asegura no colisionar con RUTs existentes."
    )

    def add_arguments(self, parser):
        parser.add_argument('--base', type=int, default=20000000, help='Número base (mín 7 dígitos). Default: 20000000')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra los cambios sin guardarlos')

    def handle(self, *args, **options):
        base = max(1000000, int(options['base']))
        dry = options['dry_run']

        tecnicos = list(Tecnico.objects.all())
        existentes = set()
        for t in tecnicos:
            if t.rut:
                existentes.add(t.rut.replace('.', '').upper())

        asignados = []
        n = base
        with transaction.atomic():
            for t in tecnicos:
                if t.rut:
                    continue
                # Encontrar siguiente número libre
                while True:
                    dv = calc_dv(n)
                    rut_clean = f"{n}{dv}"
                    if rut_clean not in existentes:
                        existentes.add(rut_clean)
                        break
                    n += 1
                rut_fmt = format_rut_number(n, dv)
                asignados.append((t.usuario.username, rut_fmt))
                if not dry:
                    t.rut = rut_fmt
                    t.save(update_fields=['rut'])
                n += 1

        if not asignados:
            self.stdout.write(self.style.WARNING('No había técnicos sin RUT.'))
            return

        if dry:
            self.stdout.write(self.style.NOTICE('DRY RUN: no se guardaron cambios'))
        self.stdout.write(self.style.SUCCESS(f"Técnicos actualizados: {0 if dry else len(asignados)} (pendientes en dry-run: {len(asignados) if dry else 0})"))
        self.stdout.write('Asignaciones:')
        for u, r in asignados:
            self.stdout.write(f" - {u} -> {r}")
