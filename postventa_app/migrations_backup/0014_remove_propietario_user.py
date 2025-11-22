from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("postventa_app", "0013_tecnico_acepta_agendamiento_online_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="propietario",
            name="user",
        ),
    ]
