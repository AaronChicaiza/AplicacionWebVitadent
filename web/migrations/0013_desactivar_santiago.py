from django.db import migrations


def desactivar_santiago(apps, schema_editor):
    Especialista = apps.get_model("web", "Especialista")
    Especialista.objects.filter(nombre_completo="Dr. Santiago Romero").update(activo=False)


class Migration(migrations.Migration):
    dependencies = [("web", "0012_paciente_nota")]
    operations = [migrations.RunPython(desactivar_santiago, migrations.RunPython.noop)]
