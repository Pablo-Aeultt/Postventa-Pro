from django.core.management.base import BaseCommand
import random
from postventa_app.models import Tecnico

nombres = [
    "Carlos", "Javier", "Matías", "Felipe", "Ignacio", "Sebastián", "Rodrigo", "Cristóbal", "Andrés", "Vicente",
    "Tomás", "Francisco", "Diego", "Gabriel", "Nicolás", "Pablo", "Hernán", "Raúl", "Eduardo", "Gonzalo"
]
apellidos = [
    "González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva", "Martínez", "Sepúlveda",
    "Morales", "Rodríguez", "López", "Fuentes", "Hernández", "Castillo", "Araya", "Reyes", "Torres", "Espinoza"
]

def generar_rut():
    num = random.randint(10000000, 25000000)
    dv = random.choice(list("0123456789K"))
    return f"{num}-{dv}"

def generar_email(nombre, apellido):
    dominios = ["gmail.com", "outlook.com", "mail.com", "yahoo.com"]
    return f"{nombre.lower()}.{apellido.lower()}@{random.choice(dominios)}"

class Command(BaseCommand):
    help = 'Actualiza todos los técnicos con nombres y datos ficticios pero realistas.'

    def handle(self, *args, **options):
        tecnicos = Tecnico.objects.all()
        actualizados = 0
        for tecnico in tecnicos:
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            tecnico.nombre = f"{nombre} {apellido}"
            tecnico.rut = generar_rut()
            tecnico.email = generar_email(nombre, apellido)
            # Teléfono chileno ficticio
            if not tecnico.telefono:
                tecnico.telefono = f"+56 9 {random.randint(10000000, 99999999)}"
            # Estado ficticio
            if not tecnico.estado:
                tecnico.estado = "activo"
            tecnico.save()
            actualizados += 1
            self.stdout.write(self.style.SUCCESS(f"Actualizado: {tecnico.nombre} | Rut: {tecnico.rut} | Email: {tecnico.email} | Teléfono: {tecnico.telefono} | Estado: {tecnico.estado}"))
        self.stdout.write(self.style.SUCCESS(f"Total técnicos actualizados: {actualizados}"))
