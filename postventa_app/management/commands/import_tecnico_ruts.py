import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from postventa_app.models import Tecnico


def normalize_rut(rut: str) -> str:
    """Normaliza un RUT básico: quita puntos, mayúscula K, asegura guion antes del dígito verificador.
    No valida matemáticamente el DV para mantenerlo simple en esta fase.
    """
    if rut is None:
        return ''
    s = str(rut).strip().replace('.', '').upper()
    if not s:
        return ''
    # Si ya tiene guion, devolver tal cual (sin puntos)
    if '-' in s:
        return s
    # Colocar guion antes del último caracter si largo mínimo
    if len(s) >= 2:
        return f"{s[:-1]}-{s[-1]}"
    return s


class Command(BaseCommand):
    help = (
        "Importa/actualiza RUT de técnicos desde CSV. "
        "Formato: username,rut (cabecera opcional)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Ruta al archivo CSV (username,rut)')
        parser.add_argument('--delimiter', default=',', help='Delimitador CSV (default ,)')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra cambios sin aplicarlos')

    def handle(self, *args, **options):
        path = options['file']
        delim = options['delimiter']
        dry = options['dry_run']

        updated, not_found, errors = 0, 0, 0
        processed = 0
        users_done = []
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delim)
                for row in reader:
                    if not row:
                        continue
                    # Saltar cabecera si detectamos 'username'
                    if processed == 0 and row[0].strip().lower() == 'username':
                        processed += 1
                        continue
                    if len(row) < 2:
                        errors += 1
                        self.stdout.write(self.style.WARNING(f"Fila inválida (se esperan 2 columnas): {row}"))
                        processed += 1
                        continue
                    username = row[0].strip()
                    rut_raw = row[1].strip()
                    if not username or not rut_raw:
                        errors += 1
                        processed += 1
                        self.stdout.write(self.style.WARNING(f"Fila con datos faltantes: {row}"))
                        continue
                    processed += 1

                    try:
                        t = Tecnico.objects.select_related('usuario').get(usuario__username=username)
                    except Tecnico.DoesNotExist:
                        not_found += 1
                        self.stdout.write(self.style.WARNING(f"No se encontró técnico para username: {username}"))
                        continue

                    rut_norm = normalize_rut(rut_raw)
                    users_done.append((username, t.rut, rut_norm))
                    if not dry:
                        t.rut = rut_norm
                        t.save(update_fields=['rut'])
                        updated += 1
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {path}")

        self.stdout.write(self.style.SUCCESS(
            f"Procesadas: {processed} | Actualizadas: {updated if not dry else 0} | No encontrados: {not_found} | Errores: {errors}"
        ))
        if users_done:
            self.stdout.write("Cambios (username: anterior -> nuevo):")
            for u, before, after in users_done:
                self.stdout.write(f" - {u}: {before or '-'} -> {after}")
