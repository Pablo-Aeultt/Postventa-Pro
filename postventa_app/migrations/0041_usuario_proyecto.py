# Generated manually on 2025-11-18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('postventa_app', '0040_encuestasatisfaccion_calificacion_solucion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='proyecto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisores', to='postventa_app.proyecto', verbose_name='Proyecto asignado'),
        ),
    ]
