import random
import hashlib
from django.core.management.base import BaseCommand
from django.db import transaction
from postventa_app.models import Tecnico


def calc_dv(num: int) -> str:
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


def format_rut(n: int) -> str:
    dv = calc_dv(n)
    s = f"{n:,}".replace(',', '.')
    return f"{s}-{dv}"


class Command(BaseCommand):
    help = (
        "Reasigna RUTs a técnicos con mayor aleatoriedad/originalidad. "
        "Estrategias: random (por defecto) o hash (determinista por username)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--strategy', choices=['random', 'hash'], default='random', help='random|hash (default random)')
        parser.add_argument('--min', dest='minv', type=int, default=7000000, help='Mínimo número base (default 7.000.000)')
        parser.add_argument('--max', dest='maxv', type=int, default=26999999, help='Máximo número base (default 26.999.999)')
        parser.add_argument('--seed', type=int, default=None, help='Semilla RNG para reproducibilidad (solo strategy=random)')
        parser.add_argument('--overwrite', action='store_true', help='Reasignar también a quienes ya tienen RUT')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra cambios')

    def handle(self, *args, **opts):
        strategy = opts['strategy']
        minv = max(1000000, int(opts['minv']))
        maxv = max(minv + 100, int(opts['maxv']))
        dry = opts['dry_run']
        overwrite = opts['overwrite']
        seed = opts['seed']

        if strategy == 'random' and seed is not None:
            random.seed(seed)

        tecnicos = list(Tecnico.objects.select_related('usuario').all())
        pool_size = maxv - minv + 1
        if pool_size < len(tecnicos):
            self.stdout.write(self.style.WARNING('Rango muy pequeño comparado con la cantidad de técnicos.'))

        # Conjunto de RUTs limpios usados (para no colisionar)
        usados = set()
        for t in tecnicos:
            if t.rut and not overwrite:
                usados.add((t.rut or '').replace('.', '').upper())

        asignaciones = []

        def take_number_for(username: str) -> int:
            if strategy == 'hash':
                h = int(hashlib.sha256((username or '').encode('utf-8')).hexdigest(), 16)
                return minv + (h % pool_size)
            # random strategy
            return random.randint(minv, maxv)

        with transaction.atomic():
            for t in tecnicos:
                if t.rut and not overwrite:
                    continue
                # Intentar asignar sin colisiones (reintentos acotados)
                reintentos = 0
                while True:
                    base = take_number_for(t.usuario.username)
                    dv = calc_dv(base)
                    clean = f"{base}{dv}"
                    if clean not in usados:
                        usados.add(clean)
                        rut_fmt = f"{base:,}".replace(',', '.') + f"-{dv}"
                        asignaciones.append((t.usuario.username, t.rut, rut_fmt))
                        if not dry:
                            t.rut = rut_fmt
                            t.save(update_fields=['rut'])
                        break
                    reintentos += 1
                    if reintentos > 50 and strategy == 'hash':
                        # En hash (determinista), si colisiona, desplazamos
                        base = ((base + reintentos) - minv) % pool_size + minv
                        dv = calc_dv(base)
                        clean = f"{base}{dv}"
                        if clean not in usados:
                            usados.add(clean)
                            rut_fmt = f"{base:,}".replace(',', '.') + f"-{dv}"
                            asignaciones.append((t.usuario.username, t.rut, rut_fmt))
                            if not dry:
                                t.rut = rut_fmt
                                t.save(update_fields=['rut'])
                            break

        if not asignaciones:
            self.stdout.write(self.style.WARNING('No hubo reasignaciones (quizá faltó --overwrite).'))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Reasignaciones: {len(asignaciones)} {'(DRY RUN)' if dry else ''}"
        ))
        self.stdout.write('Detalle (username: antes -> después):')
        for u, before, after in asignaciones:
            self.stdout.write(f" - {u}: {before or '-'} -> {after}")
