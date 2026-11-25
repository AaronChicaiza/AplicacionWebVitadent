from django.db import migrations, models

import web.models


CATALOGO = [
    ("Panorámica", "Rayos-X"),
    ("Periapical", "Rayos-X"),
    ("Lateral de cráneo", "Rayos-X"),
    ("Carpal", "Rayos-X"),
    ("Diagnóstico general", "Odontología general"),
    ("Limpieza dental", "Odontología general"),
    ("Extracciones generales", "Odontología general"),
    ("Sellantes", "Odontología general"),
    ("Diagnóstico y plan de tratamiento de cirugía ortognática", "Ortodoncia"),
    ("Brackets convencionales", "Ortodoncia"),
    ("Brackets de autoligado", "Ortodoncia"),
    ("Brackets linguales", "Ortodoncia"),
    ("Invisalign", "Ortodoncia"),
    ("Ortopedia", "Ortodoncia"),
    ("Técnica 4x2", "Ortodoncia"),
    ("Muelas del juicio", "Cirugía maxilofacial"),
    ("Frenectomías", "Cirugía maxilofacial"),
    ("Bichectomías", "Cirugía maxilofacial"),
    ("Lipopapada", "Cirugía maxilofacial"),
    ("Cirugías orales de alta complejidad", "Cirugía maxilofacial"),
    ("Blanqueamiento dental", "Rehabilitación oral"),
    ("Diseño de sonrisa", "Rehabilitación oral"),
    ("Prótesis total", "Rehabilitación oral"),
    ("Prótesis removible", "Rehabilitación oral"),
    ("Prótesis fijas", "Rehabilitación oral"),
    ("Aparatos ortopédicos", "Odontopediatría"),
    ("Endodoncias", "Odontopediatría"),
    ("Brackets para niños", "Odontopediatría"),
    ("Limpiezas", "Odontopediatría"),
    ("Calzas", "Odontopediatría"),
    ("Extracciones infantiles", "Odontopediatría"),
    ("Alivio del dolor", "Endodoncia"),
    ("Apicectomías", "Endodoncia"),
    ("Pernos", "Endodoncia"),
    ("Implantes unitarios", "Implantología"),
    ("Prótesis sobre implantes", "Implantología"),
    ("Regeneraciones óseas", "Implantología"),
    ("Injertos", "Implantología"),
]


def cargar_catalogo(apps, schema_editor):
    Tratamiento = apps.get_model("web", "Tratamiento")
    nombres = [nombre for nombre, _area in CATALOGO]
    Tratamiento.objects.exclude(nombre__in=nombres).update(activo=False)
    for nombre, area in CATALOGO:
        tratamiento, creado = Tratamiento.objects.get_or_create(
            nombre=nombre,
            defaults={"area": area, "activo": True, "duracion_minutos": None},
        )
        if tratamiento.area != area or not tratamiento.activo:
            tratamiento.area = area
            tratamiento.activo = True
            tratamiento.save(update_fields=["area", "activo"])


class Migration(migrations.Migration):
    dependencies = [("web", "0009_cita_atendida_en_cita_monto_ingreso")]

    operations = [
        migrations.RunPython(cargar_catalogo, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="tratamiento",
            name="duracion_minutos",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Mínimo 15 minutos; aumenta en intervalos de 15. Si se deja vacío, la cita usa 30 minutos.",
                null=True,
                validators=[web.models.validar_duracion_tratamiento],
            ),
        ),
    ]
