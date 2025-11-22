# Generated migration for updating GestionEscombros with ubicacion_exacta

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postventa_app', '0034_agregar_retiro_escombros'),
    ]

    operations = [
        # Agregar campo ubicacion_exacta
        migrations.AddField(
            model_name='gestionescombros',
            name='ubicacion_exacta',
            field=models.TextField(
                null=True,
                blank=True,
                verbose_name='Ubicación exacta',
                help_text='Punto donde se deberán retirar los escombros'
            ),
        ),
        
        # Actualizar tipo_escombro para usar choices
        migrations.AlterField(
            model_name='gestionescombros',
            name='tipo_escombro',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('construccion', 'Escombros de construcción'),
                    ('muebles', 'Muebles'),
                    ('miscelaneo', 'Misceláneos'),
                    ('otro', 'Otro'),
                ],
                null=True,
                blank=True,
                verbose_name='Tipo de escombro'
            ),
        ),
        
        # Actualizar verbose_name de volumen_m3
        migrations.AlterField(
            model_name='gestionescombros',
            name='volumen_m3',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=0,
                verbose_name='Volumen estimado (m³)'
            ),
        ),
    ]
