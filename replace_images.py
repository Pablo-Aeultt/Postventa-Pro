import os
import urllib.request
from pathlib import Path
from PIL import Image
from io import BytesIO
import time

# Directorio de destino
project_root = Path(__file__).parent
media_dir = project_root / "media" / "evidencias"
media_dir.mkdir(parents=True, exist_ok=True)

# URLs directas de imágenes de Pexels (interiores de casas y departamentos)
image_urls = [
    "https://images.pexels.com/photos/1350789/pexels-photo-1350789.jpeg",    # Interior moderno
    "https://images.pexels.com/photos/1457842/pexels-photo-1457842.jpeg",    # Sala de estar
    "https://images.pexels.com/photos/2062426/pexels-photo-2062426.jpeg",    # Dormitorio
    "https://images.pexels.com/photos/279810/pexels-photo-279810.jpeg",      # Cocina
    "https://images.pexels.com/photos/1866149/pexels-photo-1866149.jpeg",    # Baño moderno
    "https://images.pexels.com/photos/2251477/pexels-photo-2251477.jpeg",    # Pasillo apartamento
    "https://images.pexels.com/photos/1350789/pexels-photo-1350789.jpeg",    # Estancia
    "https://images.pexels.com/photos/1454496/pexels-photo-1454496.jpeg",    # Comedor
]

def download_image(url, filename):
    """Descarga una imagen de una URL y la guarda"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read()
        
        # Convertir a JPEG
        img = Image.open(BytesIO(content))
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Redimensionar si es muy grande
        img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        filepath = media_dir / filename
        img.save(filepath, 'JPEG', quality=85)
        print(f"✓ Descargada: {filename}")
        return True
    except Exception as e:
        print(f"✗ Error descargando {filename}: {e}")
        return False

print("Iniciando descarga de imágenes de interiores...")
print(f"Directorio destino: {media_dir}\n")

# Eliminar imágenes antiguas
print("Eliminando imágenes anteriores...")
deleted_count = 0
for file in media_dir.glob("*"):
    if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.jfif']:
        try:
            file.unlink()
            print(f"Eliminado: {file.name}")
            deleted_count += 1
        except Exception as e:
            print(f"Error eliminando {file.name}: {e}")

print(f"\nEliminadas {deleted_count} imágenes antiguas")
print("\nDescargando nuevas imágenes de interiores...\n")

# Descargar imágenes
success = 0
for i, url in enumerate(image_urls, 1):
    filename = f"interior_{i:02d}.jpg"
    if download_image(url, filename):
        success += 1
    time.sleep(1)  # Esperar entre descargas

print(f"\n{'='*60}")
print(f"✓ Proceso completado: {success}/{len(image_urls)} imágenes descargadas")
print(f"Ubicación: {media_dir}")
print(f"{'='*60}")
