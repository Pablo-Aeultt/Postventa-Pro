from django.core.management.base import BaseCommand
from postventa_app.models import Tecnico

class Command(BaseCommand):
    help = "Lista nombres, RUT y correo de todos los técnicos (CSV por stdout)."

    def add_arguments(self, parser):
        parser.add_argument('--delimiter', default=',', help='Delimitador CSV, default ","')

    def handle(self, *args, **opts):
        delim = opts['delimiter']
        self.stdout.write(f"Nombre completo{delim}RUT{delim}Email")
        tecnicos = (
            Tecnico.objects
            .select_related('usuario')
            .order_by('usuario__first_name', 'usuario__last_name', 'usuario__username')
        )
        for t in tecnicos:
            user = t.usuario
            nombre = (user.get_full_name() or user.username).strip()
            rut = (t.rut or '').strip()
            email = (user.email or t.email_corporativo or '').strip()
            self.stdout.write(f"{nombre}{delim}{rut}{delim}{email}")
