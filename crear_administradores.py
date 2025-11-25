#!/usr/bin/env python
"""
Script para crear 3 administradores, uno por cada constructora.
Ejecutar con: python manage.py shell < crear_administradores.py
O dentro de Django shell:
    exec(open('crear_administradores.py').read())
"""

from django.contrib.auth.models import User
from postventa_app.models import Constructora, Perfil

# Datos de los administradores a crear
ADMINISTRADORES = [
    {
        'username': 'admin_aconcagua',
        'email': 'admin@aconcagua.cl',
        'password': 'AconcaguaAdmin2025!',
        'first_name': 'Admin',
        'last_name': 'Aconcagua',
        'constructora_id': 1,
    },
    {
        'username': 'admin_socovesa',
        'email': 'admin@socovesa.cl',
        'password': 'SocoesaAdmin2025!',
        'first_name': 'Admin',
        'last_name': 'Socovesa',
        'constructora_id': 2,
    },
    {
        'username': 'admin_salfacorp',
        'email': 'admin@salfacorp.com',
        'password': 'SalfacorpAdmin2025!',
        'first_name': 'Admin',
        'last_name': 'SalfaCorp',
        'constructora_id': 3,
    },
]

print("=" * 60)
print("Creando Administradores por Constructora")
print("=" * 60)

for admin_data in ADMINISTRADORES:
    try:
        constructora = Constructora.objects.get(id_constructora=admin_data['constructora_id'])
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=admin_data['username']).exists():
            print(f"⚠️  Usuario {admin_data['username']} ya existe. Saltando...")
            continue
        
        # Crear usuario
        user = User.objects.create_superuser(
            username=admin_data['username'],
            email=admin_data['email'],
            password=admin_data['password'],
            first_name=admin_data['first_name'],
            last_name=admin_data['last_name'],
        )
        
        # Crear perfil de administrador
        perfil, created = Perfil.objects.get_or_create(
            user=user,
            defaults={
                'rol': 'administrador',
                'rut': constructora.rut,
            }
        )
        
        print(f"✅ Administrador creado: {admin_data['username']}")
        print(f"   Email: {admin_data['email']}")
        print(f"   Constructora: {constructora.razon_social}")
        print(f"   Contraseña: {admin_data['password']}")
        print()
        
    except Constructora.DoesNotExist:
        print(f"❌ Constructora con ID {admin_data['constructora_id']} no encontrada")
    except Exception as e:
        print(f"❌ Error al crear {admin_data['username']}: {str(e)}")

print("=" * 60)
print("Proceso completado")
print("=" * 60)
