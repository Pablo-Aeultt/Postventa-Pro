from django.core.management.base import BaseCommand
from postventa_app.models import Categoria

class Command(BaseCommand):
    help = 'Agrega las categorías faltantes: Grietas y Fisuras, Ventanas y Vidrios, Otros'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Agregando nuevas categorías...'))
        
        # Mostrar categorías actuales
        cats_actuales = Categoria.objects.all().order_by('nombre')
        self.stdout.write(f'\nCategorías actuales: {cats_actuales.count()}')
        for cat in cats_actuales:
            self.stdout.write(f'  - {cat.nombre}')
        
        # Nuevas categorías a agregar
        nuevas_categorias = [
            'Grietas y Fisuras',
            'Ventanas y Vidrios',
            'Otros'
        ]
        
        self.stdout.write(self.style.WARNING(f'\n\nAgregando {len(nuevas_categorias)} nuevas categorías...'))
        
        categorias_agregadas = []
        categorias_existentes = []
        
        for nombre_cat in nuevas_categorias:
            categoria, created = Categoria.objects.get_or_create(
                nombre=nombre_cat
            )
            
            if created:
                categorias_agregadas.append(categoria.nombre)
                self.stdout.write(self.style.SUCCESS(f'  ✓ Creada: {categoria.nombre}'))
            else:
                categorias_existentes.append(categoria.nombre)
                self.stdout.write(self.style.WARNING(f'  ⚠ Ya existe: {categoria.nombre}'))
        
        # Mostrar resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\nRESUMEN:'))
        self.stdout.write(f'  Categorías agregadas: {len(categorias_agregadas)}')
        if categorias_agregadas:
            for cat in categorias_agregadas:
                self.stdout.write(f'    + {cat}')
        
        if categorias_existentes:
            self.stdout.write(f'\n  Categorías que ya existían: {len(categorias_existentes)}')
            for cat in categorias_existentes:
                self.stdout.write(f'    = {cat}')
        
        # Mostrar todas las categorías finales
        cats_finales = Categoria.objects.all().order_by('nombre')
        self.stdout.write(f'\n\nCategorías finales ({cats_finales.count()}):\n')
        for i, cat in enumerate(cats_finales, 1):
            # Marcar las nuevas con emoji especial
            emoji = '🆕' if cat.nombre in categorias_agregadas else '✓'
            self.stdout.write(f'  {emoji} {i}. {cat.nombre}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✅ ¡Categorías agregadas exitosamente!'))
