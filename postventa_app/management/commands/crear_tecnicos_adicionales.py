from django.core.management.base import BaseCommand
import random
from postventa_app.models import Tecnico, Constructora, Especialidad

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
    return f"{nombre.lower()}.{apellido.lower()}@mail.com"

class Command(BaseCommand):
    help = 'Crea técnicos adicionales con datos ficticios y los asigna a constructoras y especialidades.'

    def handle(self, *args, **options):
        constructoras = list(Constructora.objects.all())
        especialidades = list(Especialidad.objects.all())
        cantidad = 30
        creados = 0
        for i in range(cantidad):
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            rut = generar_rut()
            email = generar_email(nombre, apellido)
            constructora = random.choice(constructoras)
            especialidad = random.choice(especialidades)
            tecnico, created = Tecnico.objects.get_or_create(
                rut=rut,
                defaults={
                    "nombre": f"{nombre} {apellido}",
                    "email": email,
                    "constructora": constructora,
                    "especialidad": especialidad,
                }
            )
                if created:
                    creados += 1
                    self.stdout.write(self.style.SUCCESS(f"Creado: {tecnico.nombre} | Rut: {tecnico.rut} | Email: {tecnico.email} | {constructora.razon_social} | {especialidad.nombre}"))
                else:
                    self.stdout.write(f"Ya existe: {tecnico.nombre} | Rut: {tecnico.rut}")
        self.stdout.write(self.style.SUCCESS(f"Total técnicos creados: {creados}"))
