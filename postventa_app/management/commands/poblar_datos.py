from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from postventa_app.models import (
    Constructora, Propietario, Proyecto, Categoria, Tecnico, 
    DisponibilidadTecnico, Reclamo
)
from datetime import date, time, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba para el sistema de agendamiento'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando población de datos...'))
        
        # 1. Crear Constructora
        constructora, created = Constructora.objects.get_or_create(
            rut='76.123.456-7',
            defaults={
                'razon_social': 'Constructora Inmobiliaria S.A.',
                'nombre_comercial': 'InmoSA',
                'email_principal': 'contacto@inmosa.cl',
                'telefono': '+56912345678',
                'direccion': 'Av. Apoquindo 4800, Las Condes, Santiago',
                'plan': 'profesional',
                'fecha_inicio_contrato': date.today() - timedelta(days=180),
                'estado': 'activo'
            }
        )
        self.stdout.write(f'✓ Constructora: {constructora.razon_social}')
        
        # 2. Crear Categorías
        categorias_data = [
            'Plomería',
            'Electricidad',
            'Pintura',
            'Carpintería',
            'Cerrajería',
            'Filtraciones',
            'Instalaciones Sanitarias',
            'Sistema de Calefacción'
        ]
        
        categorias = []
        for nombre in categorias_data:
            cat, created = Categoria.objects.get_or_create(nombre=nombre)
            categorias.append(cat)
            if created:
                self.stdout.write(f'✓ Categoría: {nombre}')
        
        # 3. Crear Proyecto
        proyecto, created = Proyecto.objects.get_or_create(
            codigo='PROY-001',
            defaults={
                'constructora': constructora,
                'nombre': 'Condominio Las Palmas',
                'ubicacion': 'Av. Las Condes 12345, Santiago',
                'region': 'Metropolitana',
                'comuna': 'Las Condes',
                'cantidad_unidades': 120,
                'fecha_entrega': date.today() - timedelta(days=365),
                'estado': 'garantia'
            }
        )
        self.stdout.write(f'✓ Proyecto: {proyecto.nombre}')
        
        # 4. Crear Técnicos con usuarios (múltiples por especialidad)
        tecnicos_data = [
            # Plomería (3 técnicos)
            {
                'username': 'juan.perez',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'email': 'juan.perez@inmosa.cl',
                'especialidad': 'Plomería',
                'categorias': ['Plomería', 'Filtraciones', 'Instalaciones Sanitarias'],
                'telefono': '+56987654321',
                'calificacion': 4.8
            },
            {
                'username': 'pedro.morales',
                'first_name': 'Pedro',
                'last_name': 'Morales',
                'email': 'pedro.morales@inmosa.cl',
                'especialidad': 'Plomería',
                'categorias': ['Plomería', 'Filtraciones'],
                'telefono': '+56987654324',
                'calificacion': 4.5
            },
            {
                'username': 'luis.ramirez',
                'first_name': 'Luis',
                'last_name': 'Ramírez',
                'email': 'luis.ramirez@inmosa.cl',
                'especialidad': 'Plomería',
                'categorias': ['Plomería', 'Instalaciones Sanitarias'],
                'telefono': '+56987654325',
                'calificacion': 4.6
            },
            # Electricidad (3 técnicos)
            {
                'username': 'maria.gonzalez',
                'first_name': 'María',
                'last_name': 'González',
                'email': 'maria.gonzalez@inmosa.cl',
                'especialidad': 'Electricidad',
                'categorias': ['Electricidad'],
                'telefono': '+56987654322',
                'calificacion': 4.9
            },
            {
                'username': 'roberto.castro',
                'first_name': 'Roberto',
                'last_name': 'Castro',
                'email': 'roberto.castro@inmosa.cl',
                'especialidad': 'Electricidad',
                'categorias': ['Electricidad'],
                'telefono': '+56987654326',
                'calificacion': 4.7
            },
            {
                'username': 'andrea.lopez',
                'first_name': 'Andrea',
                'last_name': 'López',
                'email': 'andrea.lopez@inmosa.cl',
                'especialidad': 'Electricidad',
                'categorias': ['Electricidad'],
                'telefono': '+56987654327',
                'calificacion': 4.8
            },
            # Pintura (3 técnicos)
            {
                'username': 'carlos.silva',
                'first_name': 'Carlos',
                'last_name': 'Silva',
                'email': 'carlos.silva@inmosa.cl',
                'especialidad': 'Pintura',
                'categorias': ['Pintura', 'Carpintería'],
                'telefono': '+56987654323',
                'calificacion': 4.4
            },
            {
                'username': 'jose.torres',
                'first_name': 'José',
                'last_name': 'Torres',
                'email': 'jose.torres@inmosa.cl',
                'especialidad': 'Pintura',
                'categorias': ['Pintura'],
                'telefono': '+56987654328',
                'calificacion': 4.6
            },
            {
                'username': 'miguel.vargas',
                'first_name': 'Miguel',
                'last_name': 'Vargas',
                'email': 'miguel.vargas@inmosa.cl',
                'especialidad': 'Pintura',
                'categorias': ['Pintura', 'Carpintería'],
                'telefono': '+56987654329',
                'calificacion': 4.5
            },
            # Carpintería (2 técnicos)
            {
                'username': 'fernando.ruiz',
                'first_name': 'Fernando',
                'last_name': 'Ruiz',
                'email': 'fernando.ruiz@inmosa.cl',
                'especialidad': 'Carpintería',
                'categorias': ['Carpintería'],
                'telefono': '+56987654330',
                'calificacion': 4.7
            },
            {
                'username': 'diego.soto',
                'first_name': 'Diego',
                'last_name': 'Soto',
                'email': 'diego.soto@inmosa.cl',
                'especialidad': 'Carpintería',
                'categorias': ['Carpintería'],
                'telefono': '+56987654331',
                'calificacion': 4.8
            },
            # Cerrajería (2 técnicos)
            {
                'username': 'sergio.bravo',
                'first_name': 'Sergio',
                'last_name': 'Bravo',
                'email': 'sergio.bravo@inmosa.cl',
                'especialidad': 'Cerrajería',
                'categorias': ['Cerrajería'],
                'telefono': '+56987654332',
                'calificacion': 4.9
            },
            {
                'username': 'pablo.medina',
                'first_name': 'Pablo',
                'last_name': 'Medina',
                'email': 'pablo.medina@inmosa.cl',
                'especialidad': 'Cerrajería',
                'categorias': ['Cerrajería'],
                'telefono': '+56987654333',
                'calificacion': 4.6
            },
            # Sistema de Calefacción (2 técnicos)
            {
                'username': 'ricardo.parra',
                'first_name': 'Ricardo',
                'last_name': 'Parra',
                'email': 'ricardo.parra@inmosa.cl',
                'especialidad': 'Sistema de Calefacción',
                'categorias': ['Sistema de Calefacción'],
                'telefono': '+56987654334',
                'calificacion': 4.7
            },
            {
                'username': 'gonzalo.reyes',
                'first_name': 'Gonzalo',
                'last_name': 'Reyes',
                'email': 'gonzalo.reyes@inmosa.cl',
                'especialidad': 'Sistema de Calefacción',
                'categorias': ['Sistema de Calefacción'],
                'telefono': '+56987654335',
                'calificacion': 4.8
            }
        ]
        
        tecnicos = []
        for data in tecnicos_data:
            # Crear o obtener usuario
            user, user_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email']
                }
            )
            
            if user_created:
                user.set_password('tecnico123')
                user.save()
            
            # Crear o obtener técnico
            tecnico, tec_created = Tecnico.objects.get_or_create(
                usuario=user,
                defaults={
                    'constructora': constructora,
                    'especialidad': data['especialidad'],
                    'telefono': data['telefono'],
                    'email_corporativo': data['email'],
                    'estado': 'disponible',
                    'acepta_agendamiento_online': True,
                    'calificacion_promedio': data.get('calificacion', 4.5),
                    'cantidad_calificaciones': 15,
                    'casos_completados': 45
                }
            )
            
            # Asignar especialidades (categorías)
            if tec_created or tecnico.especialidades.count() == 0:
                for cat_nombre in data['categorias']:
                    cat = Categoria.objects.get(nombre=cat_nombre)
                    tecnico.especialidades.add(cat)
            
            # Asignar proyecto
            if tec_created or tecnico.proyectos_asignados.count() == 0:
                tecnico.proyectos_asignados.add(proyecto)
            
            tecnicos.append(tecnico)
            self.stdout.write(f'✓ Técnico: {user.get_full_name()} - {tecnico.especialidad}')
        
        # 5. Crear disponibilidades para cada técnico (Lunes a Viernes, 9:00-18:00)
        for tecnico in tecnicos:
            if tecnico.disponibilidades.count() == 0:
                # Lunes a Viernes
                for dia in range(0, 5):
                    # Mañana: 9:00 - 13:00
                    DisponibilidadTecnico.objects.create(
                        tecnico=tecnico,
                        dia_semana=dia,
                        hora_inicio=time(9, 0),
                        hora_fin=time(13, 0),
                        activo=True
                    )
                    # Tarde: 14:00 - 18:00
                    DisponibilidadTecnico.objects.create(
                        tecnico=tecnico,
                        dia_semana=dia,
                        hora_inicio=time(14, 0),
                        hora_fin=time(18, 0),
                        activo=True
                    )
                self.stdout.write(f'  ✓ Disponibilidad creada para {tecnico.usuario.get_full_name()}')
        
        # 6. Crear propietarios de ejemplo (si no existen)
        propietarios_data = [
            {
                'rut': '12.345.678-9',
                'nombre': 'Pedro Ramírez',
                'email': 'pedro.ramirez@gmail.com',
                'telefono': '+56912345001',
                'unidad': 'Depto 101'
            },
            {
                'rut': '98.765.432-1',
                'nombre': 'Ana Torres',
                'email': 'ana.torres@gmail.com',
                'telefono': '+56912345002',
                'unidad': 'Depto 205'
            }
        ]
        
        for data in propietarios_data:
            prop, created = Propietario.objects.get_or_create(
                rut=data['rut'],
                defaults={
                    'nombre': data['nombre'],
                    'email': data['email'],
                    'telefono': data['telefono'],
                    'direccion': f'Condominio Las Palmas, {data["unidad"]}',
                    'proyecto': proyecto,
                    'unidad': data['unidad'],
                    'estado': 'activo'
                }
            )
            
            # Crear usuario para el propietario
            if created and not prop.user:
                rut_limpio = data['rut'].replace('.', '').replace('-', '')
                user_prop, _ = User.objects.get_or_create(
                    username=rut_limpio,
                    defaults={
                        'email': data['email']
                    }
                )
                user_prop.set_password('propietario123')
                user_prop.save()
                prop.user = user_prop
                prop.save()
            
            if created:
                self.stdout.write(f'✓ Propietario: {data["nombre"]} - {data["unidad"]}')
        
        self.stdout.write(self.style.SUCCESS('\n¡Datos de prueba creados exitosamente!'))
        self.stdout.write(self.style.SUCCESS('\n=== CREDENCIALES DE ACCESO ==='))
        self.stdout.write('Técnicos:')
        self.stdout.write('  - juan.perez / tecnico123')
        self.stdout.write('  - maria.gonzalez / tecnico123')
        self.stdout.write('  - carlos.silva / tecnico123')
        self.stdout.write('\nPropietarios:')
        self.stdout.write('  - 12.345.678-9 / propietario123')
        self.stdout.write('  - 98.765.432-1 / propietario123')
