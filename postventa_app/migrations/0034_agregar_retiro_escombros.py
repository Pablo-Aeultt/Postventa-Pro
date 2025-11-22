# Generated migration for adding retiro_escombros fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postventa_app', '0033_agregar_retiro_escombros'),
    ]

    operations = [
        # Agregar campo requiere_retiro_escombros a Reclamo
        migrations.AddField(
            model_name='reclamo',
            name='requiere_retiro_escombros',
            field=models.BooleanField(default=False, verbose_name='Requiere retiro de escombros'),
        ),
        
        # Mejorar campos en GestionEscombros
        migrations.AlterField(
            model_name='gestionescombros',
            name='estado',
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('programado', 'Programado'),
                    ('en_ejecucion', 'En Ejecución'),
                    ('completado', 'Completado'),
                    ('cancelado', 'Cancelado'),
                ],
                default='pendiente',
                verbose_name='Estado'
            ),
        ),
    ]
