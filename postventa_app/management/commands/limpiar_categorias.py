from django.core.management.base import BaseCommand
from postventa_app.models import Categoria, Tecnico


class Command(BaseCommand):
    help = 'Limpia categorías duplicadas y obsoletas de la base de datos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Limpiando categorías duplicadas...'))
        
        # Categorías que queremos mantener (las del comando poblar_datos)
        categorias_validas = [
            'Plomería',
            'Electricidad',
            'Pintura',
            'Carpintería',
            'Cerrajería',
            'Filtraciones',
            'Instalaciones Sanitarias',
            'Sistema de Calefacción'
        ]
        
        # Obtener todas las categorías
        todas_categorias = Categoria.objects.all()
        self.stdout.write(f'Total de categorías antes: {todas_categorias.count()}')
        
        # Eliminar categorías que NO están en la lista válida
        categorias_eliminar = Categoria.objects.exclude(nombre__in=categorias_validas)
        count_eliminadas = categorias_eliminar.count()
        
        if count_eliminadas > 0:
            self.stdout.write(f'Eliminando {count_eliminadas} categorías obsoletas:')
            for cat in categorias_eliminar:
                self.stdout.write(f'  - {cat.nombre} (ID: {cat.id})')
            
            categorias_eliminar.delete()
        
        # Mostrar categorías finales
        categorias_finales = Categoria.objects.all().order_by('nombre')
        self.stdout.write(f'\nCategorías finales ({categorias_finales.count()}):')
        for cat in categorias_finales:
            tecnicos_count = cat.tecnicos_especializados.count()
            self.stdout.write(f'  ✓ {cat.nombre} (ID: {cat.id}) - {tecnicos_count} técnicos')
        
        self.stdout.write(self.style.SUCCESS('\n¡Limpieza completada exitosamente!'))
