import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plataforma_postventa.settings')
django.setup()

from postventa_app.models import Proyecto, Propietario, Tecnico

print("=" * 70)
print("INFORMACIÓN DE PROYECTOS, PROPIETARIOS Y TÉCNICOS")
print("=" * 70)

proyectos = Proyecto.objects.all().order_by('nombre')

for proyecto in proyectos:
    print(f"\n📍 PROYECTO: {proyecto.nombre}")
    print(f"   ID: {proyecto.id_proyecto}")
    
    # Propietarios
    propietarios = Propietario.objects.filter(proyecto=proyecto)
    print(f"   👥 Propietarios: {propietarios.count()}")
    
    # Técnicos (por constructora)
    if proyecto.constructora:
        tecnicos = Tecnico.objects.filter(constructora=proyecto.constructora)
        print(f"   🔧 Técnicos ({proyecto.constructora.razon_social}): {tecnicos.count()}")
    else:
        print(f"   🔧 Técnicos: 0 (sin constructora asignada)")

print("\n" + "=" * 70)
print("RESUMEN TOTAL")
print("=" * 70)
print(f"Total Proyectos: {Proyecto.objects.count()}")
print(f"Total Propietarios: {Propietario.objects.count()}")
print(f"Total Técnicos: {Tecnico.objects.count()}")
