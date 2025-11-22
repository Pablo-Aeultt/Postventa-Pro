from django.core.management.base import BaseCommand
from postventa_app.models import Tecnico, Cliente

class Command(BaseCommand):
    help = 'Exporta una tabla de Nombre, RUT, Correo y contraseña de propietarios y técnicos.'

    def handle(self, *args, **options):
        import csv
        output_path = 'usuarios_exportados.csv'
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['NOMBRE', 'RUT', 'CORREO', 'ESPECIALIDAD', 'CONSTRUCTORA', 'CONTRASEÑA'])
            # Técnicos
            for tecnico in Tecnico.objects.all():
                nombre = tecnico.nombre
                rut = tecnico.rut
                correo = getattr(tecnico, 'email', '') or ''
                especialidad = getattr(tecnico, 'especialidad', None)
                especialidad_nombre = especialidad.nombre if especialidad else ''
                constructora = getattr(tecnico, 'constructora', None)
                constructora_nombre = constructora.razon_social if constructora else ''
                writer.writerow([nombre, rut, correo, especialidad_nombre, constructora_nombre, 'tecnico123'])
            # Propietarios
            for propietario in Cliente.objects.all():
                nombre = propietario.nombre
                rut = propietario.rut
                correo = getattr(propietario, 'email', '') or ''
                writer.writerow([nombre, rut, correo, '', '', 'propietario123'])
        self.stdout.write(f"Exportación completada en {output_path}")
