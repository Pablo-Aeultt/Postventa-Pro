# Generated migration for updating tipos_escombro choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postventa_app', '0035_gestionescombros_ubicacion_exacta'),
    ]

    operations = [
        # Actualizar campo tipo_escombro con nuevos choices
        migrations.AlterField(
            model_name='gestionescombros',
            name='tipo_escombro',
            field=models.CharField(
                blank=True,
                choices=[
                    ('construccion', 'Construcción'),
                    ('muebles_madera', 'Muebles o madera'),
                    ('metales', 'Metales'),
                    ('plasticos_carton', 'Plásticos / cartón'),
                    ('vidrio', 'Vidrio'),
                    ('mixto', 'Mixto'),
                    ('otro', 'Otro'),
                ],
                max_length=30,
                null=True,
                verbose_name='Tipo de escombro'
            ),
        ),
    ]
