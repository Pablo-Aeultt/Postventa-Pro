import os
import sys
from pathlib import Path

# Agregar el proyecto a la ruta de Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plataforma_postventa.settings')

import django
django.setup()

from postventa_app.models import ArchivoEvidencia

print("Corrigiendo rutas de imágenes en la base de datos...\n")

# Obtener todos los archivos
archivos = ArchivoEvidencia.objects.filter(archivo__isnull=False).exclude(archivo='')

print(f"Procesando {archivos.count()} archivos...\n")

corrected_count = 0

for archivo in archivos:
    ruta_actual = str(archivo.archivo)
    ruta_nueva = ruta_actual
    
    # Cambiar rutas a las carpetas correctas
    # De: evidencias/propietario/... o evidencias/técnico/...
    # A: evidencias/propietario/... o evidencias/técnico/...
    
    # Limpiar rutas duplicadas primero
    if 'evidencias/evidencias' in ruta_nueva:
        ruta_nueva = ruta_nueva.replace('evidencias/evidencias', 'evidencias')
    
    # Asegurar que use las carpetas singular (propietario, técnico)
    if '/propietarios/' in ruta_nueva:
        ruta_nueva = ruta_nueva.replace('/propietarios/', '/propietario/')
    
    if '/tecnicos/' in ruta_nueva:
        ruta_nueva = ruta_nueva.replace('/tecnicos/', '/técnico/')
    
    # Cambiar caracteres especiales (tecnico sin acento si existe)
    if 'tecnico' in ruta_nueva.lower() and 'técnico' not in ruta_nueva:
        ruta_nueva = ruta_nueva.replace('tecnico', 'técnico')
    
    # Si la ruta cambió, actualizar
    if ruta_nueva != ruta_actual:
        archivo.archivo = ruta_nueva
        archivo.save()
        print(f"✓ ID {archivo.id_archivo}:")
        print(f"  Anterior: {ruta_actual}")
        print(f"  Nuevo:    {ruta_nueva}\n")
        corrected_count += 1

print(f"\n{'='*60}")
print(f"✓ Proceso completado: {corrected_count} rutas actualizadas")
print(f"{'='*60}")
