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
from django.core.files.base import ContentFile
from datetime import datetime

# Directorios de destino
media_dir = Path("media/evidencias")
propietario_dir = media_dir / "propietarios"
tecnico_dir = media_dir / "tecnicos"

# Crear directorios si no existen
propietario_dir.mkdir(parents=True, exist_ok=True)
tecnico_dir.mkdir(parents=True, exist_ok=True)

print("Organizando imágenes por tipo de usuario...\n")

# Obtener todas las imágenes de stock disponibles
stock_images = sorted(list(media_dir.glob("interior_*.jpg")))

if not stock_images:
    print("❌ No se encontraron imágenes de stock en media/evidencias/")
    exit(1)

print(f"✓ Encontradas {len(stock_images)} imágenes de stock\n")

# Obtener todos los archivos de evidencia
archivos = ArchivoEvidencia.objects.filter(archivo__isnull=False).exclude(archivo='').order_by('id_archivo')

print(f"Procesando {archivos.count()} archivos de evidencia...\n")

image_index = 0
propietario_count = 0
tecnico_count = 0

for archivo in archivos:
    if image_index >= len(stock_images):
        image_index = 0  # Ciclar entre imágenes
    
    stock_image_path = stock_images[image_index]
    
    try:
        # Determinar si es propietario o técnico
        is_propietario = archivo.subido_por == 'cliente'
        target_dir = propietario_dir if is_propietario else tecnico_dir
        user_type = "propietario" if is_propietario else "técnico"
        
        # Leer la imagen de stock
        with open(stock_image_path, 'rb') as f:
            file_content = f.read()
        
        # Guardar en la carpeta correspondiente
        relative_path = f"evidencias/{user_type}/{stock_image_path.name}"
        archivo.archivo.save(relative_path, ContentFile(file_content), save=True)
        archivo.nombre_original = stock_image_path.name
        archivo.fecha_subida = datetime.now()
        archivo.save()
        
        if is_propietario:
            propietario_count += 1
        else:
            tecnico_count += 1
        
        print(f"✓ Archivo ID {archivo.id_archivo}: Movido a carpeta de {user_type}")
        image_index += 1
        
    except Exception as e:
        print(f"✗ Error procesando archivo {archivo.id_archivo}: {e}")

print(f"\n{'='*60}")
print(f"✓ Proceso completado:")
print(f"  - {propietario_count} archivos de propietarios")
print(f"  - {tecnico_count} archivos de técnicos")
print(f"\n  Ubicaciones:")
print(f"  - Propietarios: {propietario_dir}")
print(f"  - Técnicos: {tecnico_dir}")
print(f"{'='*60}")
