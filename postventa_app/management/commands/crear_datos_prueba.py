from django.core.management.base import BaseCommand
from django.utils import timezone
from postventa_app.models import Constructora, Proyecto, Propietario, Categoria
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de postventa'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creando datos de prueba...'))
        
        # 1. CONSTRUCTORAS REALES
        self.stdout.write('\n📌 Creando Constructoras...')
        
        constructoras_data = [
            {
                'rut': '96517210-6',
                'razon_social': 'Socovesa S.A.',
                'nombre_comercial': 'Socovesa',
                'direccion': 'Av. Presidente Riesco 5561, Piso 18, Las Condes',
                'telefono': '+56223391000',
                'email_principal': 'contacto@socovesa.cl',
                'nombre_ejecutivo': 'Carolina Muñoz',
                'email_ejecutivo': 'cmonoz@socovesa.cl',
                'telefono_ejecutivo': '+56987654321',
                'plan': 'corporativo',
                'fecha_inicio_contrato': date(2024, 1, 1),
                'estado': 'activo',
            },
            {
                'rut': '76240079-0',
                'razon_social': 'Inmobiliaria Almagro S.A.',
                'nombre_comercial': 'Almagro',
                'direccion': 'Av. Apoquindo 3846, Las Condes',
                'telefono': '+56222070000',
                'email_principal': 'contacto@almagro.cl',
                'nombre_ejecutivo': 'Rodrigo Valenzuela',
                'email_ejecutivo': 'rvalenzuela@almagro.cl',
                'telefono_ejecutivo': '+56976543210',
                'plan': 'profesional',
                'fecha_inicio_contrato': date(2024, 3, 15),
                'estado': 'activo',
            },
            {
                'rut': '76124890-8',
                'razon_social': 'Constructora Echeverría Izquierdo S.A.',
                'nombre_comercial': 'Echeverría Izquierdo',
                'direccion': 'Av. El Bosque Norte 0440, Las Condes',
                'telefono': '+56223537000',
                'email_principal': 'contacto@eisa.cl',
                'nombre_ejecutivo': 'Patricia Soto',
                'email_ejecutivo': 'psoto@eisa.cl',
                'telefono_ejecutivo': '+56965432109',
                'plan': 'corporativo',
                'fecha_inicio_contrato': date(2023, 11, 1),
                'estado': 'activo',
            },
        ]
        
        constructoras_creadas = []
        for const_data in constructoras_data:
            constructora, created = Constructora.objects.get_or_create(
                rut=const_data['rut'],
                defaults=const_data
            )
            constructoras_creadas.append(constructora)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Constructora creada: {constructora.nombre_comercial}'))
            else:
                self.stdout.write(self.style.WARNING(f'  → Constructora ya existe: {constructora.nombre_comercial}'))
        
        # Usar la primera constructora para los ejemplos siguientes
        constructora = constructoras_creadas[0]
        
        # 2. PROYECTOS REALES
        self.stdout.write('\n📌 Creando Proyectos...')
        proyectos_data = [
            {
                'codigo': 'SOC-LAC-001',
                'nombre': 'Condominio Alto La Concepción',
                'ubicacion': 'Camino La Concepción 12.345, Penalolén',
                'comuna': 'Peñalolén',
                'region': 'Región Metropolitana',
                'cantidad_unidades': 156,
                'encargado': 'Andrés Muñoz',
                'telefono_encargado': '+56987123456',
                'fecha_inicio': date(2022, 3, 1),
                'fecha_entrega': date(2024, 6, 30),
                'estado': 'garantia',
            },
            {
                'codigo': 'ALM-VIT-002',
                'nombre': 'Edificio Nueva Costanera',
                'ubicacion': 'Av. Nueva Costanera 3756, Vitacura',
                'comuna': 'Vitacura',
                'region': 'Región Metropolitana',
                'cantidad_unidades': 48,
                'encargado': 'Claudia Reyes',
                'telefono_encargado': '+56976234567',
                'fecha_inicio': date(2023, 1, 15),
                'fecha_entrega': date(2024, 12, 20),
                'estado': 'entregado',
            },
            {
                'codigo': 'EISA-MAC-003',
                'nombre': 'Parque Macul',
                'ubicacion': 'Av. Macul 5678, Macul',
                'comuna': 'Macul',
                'region': 'Región Metropolitana',
                'cantidad_unidades': 220,
                'encargado': 'Fernando Lagos',
                'telefono_encargado': '+56965345678',
                'fecha_inicio': date(2021, 9, 1),
                'fecha_entrega': date(2024, 3, 31),
                'estado': 'garantia',
            },
            {
                'codigo': 'SOC-MAI-004',
                'nombre': 'Altos de Maipú',
                'ubicacion': 'Camino a Rinconada 2340, Maipú',
                'comuna': 'Maipú',
                'region': 'Región Metropolitana',
                'cantidad_unidades': 188,
                'encargado': 'Valentina Torres',
                'telefono_encargado': '+56954456789',
                'fecha_inicio': date(2022, 6, 15),
                'fecha_entrega': date(2024, 9, 30),
                'estado': 'garantia',
            },
            {
                'codigo': 'ALM-PRO-005',
                'nombre': 'Edificio Providencia Centro',
                'ubicacion': 'Av. Providencia 1234, Providencia',
                'comuna': 'Providencia',
                'region': 'Región Metropolitana',
                'cantidad_unidades': 72,
                'encargado': 'Marcelo Díaz',
                'telefono_encargado': '+56943567890',
                'fecha_inicio': date(2023, 4, 1),
                'fecha_entrega': date(2024, 10, 15),
                'estado': 'entregado',  # Recién entregado hace días
            },
        ]
        
        proyectos_creados = []
        for i, proyecto_data in enumerate(proyectos_data):
            # Distribuir proyectos entre las constructoras
            proyecto_data['constructora'] = constructoras_creadas[i % len(constructoras_creadas)]
            proyecto, created = Proyecto.objects.get_or_create(
                codigo=proyecto_data['codigo'],
                defaults=proyecto_data
            )
            proyectos_creados.append(proyecto)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Proyecto creado: {proyecto.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'  → Proyecto ya existe: {proyecto.nombre}'))
        
        # 3. CATEGORÍAS
        self.stdout.write('\n📌 Creando Categorías...')
        categorias_nombres = [
            'Gasfitería y Filtraciones',
            'Eléctrico',
            'Pintura y Terminaciones',
            'Carpintería y Puertas',
            'Ventanas y Vidrios',
            'Cerrajería',
            'Pisos y Revestimientos',
            'Artefactos Sanitarios',
            'Grietas y Fisuras',
            'Humedad',
        ]
        
        categorias_creadas = []
        for nombre in categorias_nombres:
            categoria, created = Categoria.objects.get_or_create(
                nombre=nombre
            )
            categorias_creadas.append(categoria)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Categoría creada: {categoria.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'  → Categoría ya existe: {categoria.nombre}'))
        
        # 4. TÉCNICOS - Comentado por ahora (requiere crear usuarios primero)
        self.stdout.write('\n📌 Técnicos...')
        self.stdout.write(self.style.WARNING('  → Los técnicos se crean desde el admin (requieren usuario)'))
        
        #5. PROPIETARIOS
        self.stdout.write('\n📌 Creando Propietarios...')
        propietarios_data = [
            # Condominio Alto La Concepción
            {
                'rut': '15234567-8',
                'nombre': 'Andrea Rodríguez Muñoz',
                'tipo_propietario': 'natural',
                'email': 'arodriguez@gmail.com',
                'telefono': '+56912345001',
                'direccion': 'Camino La Concepción 12.345, Depto 302',
                'proyecto': proyectos_creados[0],
                'unidad': 'Torre A - Depto 302',
                'estado': 'activo',
            },
            {
                'rut': '17456789-2',
                'nombre': 'Carlos Fuentes Lagos',
                'tipo_propietario': 'natural',
                'email': 'cfuentes@outlook.com',
                'telefono': '+56923456002',
                'direccion': 'Camino La Concepción 12.345, Depto 508',
                'proyecto': proyectos_creados[0],
                'unidad': 'Torre B - Depto 508',
                'estado': 'activo',
            },
            {
                'rut': '18234890-5',
                'nombre': 'Patricia González Silva',
                'tipo_propietario': 'natural',
                'email': 'pgonzalez@hotmail.com',
                'telefono': '+56934567003',
                'direccion': 'Camino La Concepción 12.345, Depto 1203',
                'proyecto': proyectos_creados[0],
                'unidad': 'Torre C - Depto 1203',
                'estado': 'activo',
            },
            # Edificio Nueva Costanera
            {
                'rut': '16789012-K',
                'nombre': 'Rodrigo Valdivia Parra',
                'tipo_propietario': 'natural',
                'email': 'rvaldivia@gmail.com',
                'telefono': '+56945678004',
                'direccion': 'Av. Nueva Costanera 3756, Depto 1801',
                'proyecto': proyectos_creados[1],
                'unidad': 'Piso 18 - Depto 1801',
                'estado': 'activo',
            },
            {
                'rut': '77123456-4',
                'nombre': 'Inmobiliaria Renta Plus S.A.',
                'tipo_propietario': 'juridica',
                'email': 'contacto@rentaplus.cl',
                'telefono': '+56956789005',
                'direccion': 'Av. Nueva Costanera 3756, Deptos varios',
                'proyecto': proyectos_creados[1],
                'unidad': 'Pisos 5-7 (Inversión)',
                'estado': 'activo',
            },
            # Parque Macul
            {
                'rut': '19012345-3',
                'nombre': 'María José Contreras Vera',
                'tipo_propietario': 'natural',
                'email': 'mjcontreras@yahoo.com',
                'telefono': '+56967890006',
                'direccion': 'Av. Macul 5678, Casa 15',
                'proyecto': proyectos_creados[2],
                'unidad': 'Casa 15',
                'estado': 'activo',
            },
            {
                'rut': '20123456-7',
                'nombre': 'Jorge Andrés Morales Díaz',
                'tipo_propietario': 'natural',
                'email': 'jmorales@gmail.com',
                'telefono': '+56978901007',
                'direccion': 'Av. Macul 5678, Casa 42',
                'proyecto': proyectos_creados[2],
                'unidad': 'Casa 42',
                'estado': 'activo',
            },
            # Altos de Maipú
            {
                'rut': '14567890-9',
                'nombre': 'Daniela Paz Soto Ramírez',
                'tipo_propietario': 'natural',
                'email': 'dpsoto@icloud.com',
                'telefono': '+56989012008',
                'direccion': 'Camino a Rinconada 2340, Depto 405',
                'proyecto': proyectos_creados[3],
                'unidad': 'Edificio 4 - Depto 405',
                'estado': 'activo',
            },
            {
                'rut': '21234567-1',
                'nombre': 'Felipe Ignacio Torres Muñoz',
                'tipo_propietario': 'natural',
                'email': 'ftorres@gmail.com',
                'telefono': '+56990123009',
                'direccion': 'Camino a Rinconada 2340, Depto 702',
                'proyecto': proyectos_creados[3],
                'unidad': 'Edificio 7 - Depto 702',
                'estado': 'activo',
            },
            # Edificio Providencia Centro
            {
                'rut': '13890123-6',
                'nombre': 'Valentina Alejandra Vásquez Bravo',
                'tipo_propietario': 'natural',
                'email': 'vvasquez@outlook.com',
                'telefono': '+56991234010',
                'direccion': 'Av. Providencia 1234, Depto 601',
                'proyecto': proyectos_creados[4],
                'unidad': 'Depto 601',
                'estado': 'activo',
            },
            {
                'rut': '76890123-2',
                'nombre': 'Inversiones Providencia Limitada',
                'tipo_propietario': 'juridica',
                'email': 'contacto@invprovidencia.cl',
                'telefono': '+56992345011',
                'direccion': 'Av. Providencia 1234, Oficinas',
                'proyecto': proyectos_creados[4],
                'unidad': 'Pisos comerciales 1-2',
                'estado': 'activo',
            },
        ]
        
        for propietario_data in propietarios_data:
            propietario, created = Propietario.objects.get_or_create(
                rut=propietario_data['rut'],
                defaults=propietario_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Propietario creado: {propietario.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'  → Propietario ya existe: {propietario.nombre}'))
        
        # RESUMEN
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ DATOS DE PRUEBA CREADOS EXITOSAMENTE'))
        self.stdout.write('='*60)
        self.stdout.write(f'📊 Constructoras: {Constructora.objects.count()}')
        self.stdout.write(f'🏗️  Proyectos: {Proyecto.objects.count()}')
        self.stdout.write(f'📁 Categorías: {Categoria.objects.count()}')
        self.stdout.write(f' Propietarios: {Propietario.objects.count()}')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('\n🎉 Ya puedes crear reclamos en: http://127.0.0.1:8000/crear/'))
