from django.core.management.base import BaseCommand
from postventa_app.models import Propietario, Proyecto
from django.contrib.auth.models import User

INMOBILIARIAS = [
    "Socovesa", "Almagro", "Echeverría Izquierdo", "Aconcagua", "Inmobiliaria Manquehue",
    "Inmobiliaria Fundamenta", "Inmobiliaria Renta Plus", "Inmobiliaria Actual", "Inmobiliaria Siena", "Inmobiliaria Paz"
]

class Command(BaseCommand):
    help = 'Crea 10 propietarios de prueba con inmobiliarias chilenas y usuarios vinculados.'

    def handle(self, *args, **options):
        import random
        nombres = [
            "Camila Rojas", "Felipe González", "Valentina Muñoz", "Jorge Herrera", "Sofía Castro",
            "Matías Paredes", "Carolina Silva", "Ignacio Soto", "Francisca Ramírez", "Sebastián Torres",
            "Diego Fuentes", "Gabriela Martínez", "Rodrigo Díaz", "Paula Contreras", "Tomás Espinoza",
            "María Fernanda López", "Cristóbal Reyes", "Daniela Bravo", "Benjamín Vega", "Antonia Castillo"
        ]
        proyectos = list(Proyecto.objects.all())
        random.shuffle(nombres)
        for i in range(10):
            nombre = random.choice(nombres)
            rut = f"3{random.randint(10000000,99999999)}-{random.choice(['K','1','2','3','4','5','6','7','8','9'])}"
            email = f"{nombre.split()[0].lower()}.{nombre.split()[1].lower()}{random.randint(1,99)}@gmail.com"
            telefono = f"+569{random.randint(10000000,99999999)}"
            direccion = f"Calle {random.randint(100,999)}, Santiago"
            proyecto = random.choice(proyectos) if proyectos else None
            unidad = f"Depto {random.randint(100,999)}"
            username = rut.replace('.', '').replace('-', '')
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='propietario123',
                    first_name=nombre.split()[0],
                    last_name=' '.join(nombre.split()[1:])
                )
            else:
                user = User.objects.get(username=username)
            propietario, created = Propietario.objects.get_or_create(
                rut=rut,
                defaults={
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'direccion': direccion,
                    'proyecto': proyecto,
                    'unidad': unidad,
                    'user': user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Propietario aleatorio creado: {nombre} ({rut}) en {proyecto}"))
            else:
                self.stdout.write(f"Propietario aleatorio ya existía: {nombre} ({rut})")
        self.stdout.write(self.style.SUCCESS("10 propietarios aleatorios y realistas creados."))
