import os
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plataforma_postventa.settings')
django.setup()

from postventa_app.models import ArchivoEvidencia
from django.core.files.base import ContentFile
from datetime import datetime

# Directorio de imágenes
media_dir = Path("media/evidencias")
new_images = list(media_dir.glob("interior_*.jpg"))

if not new_images:
    print("❌ No se encontraron imágenes nuevas en media/evidencias/")
    exit(1)

print(f"✓ Encontradas {len(new_images)} imágenes nuevas\n")

# Obtener todos los archivos de evidencia
archivos = ArchivoEvidencia.objects.filter(archivo__isnull=False).exclude(archivo='')

print(f"Actualizando {archivos.count()} archivos de evidencia...\n")

image_index = 0
updated_count = 0

for archivo in archivos:
    if image_index >= len(new_images):
        image_index = 0  # Ciclar entre imágenes si hay más archivos que imágenes
    
    try:
        new_image_path = new_images[image_index]
        
        # Leer la nueva imagen
        with open(new_image_path, 'rb') as f:
            file_content = f.read()
        
        # Actualizar el archivo
        archivo.archivo.save(new_image_path.name, ContentFile(file_content), save=True)
        archivo.nombre_original = new_image_path.name
        archivo.fecha_subida = datetime.now()
        archivo.save()
        
        print(f"✓ Archivo ID {archivo.id_archivo}: Actualizado con {new_image_path.name}")
        updated_count += 1
        image_index += 1
        
    except Exception as e:
        print(f"✗ Error actualizando archivo {archivo.id_archivo}: {e}")

print(f"\n{'='*60}")
print(f"✓ Proceso completado: {updated_count} archivos actualizados")
print(f"{'='*60}")
